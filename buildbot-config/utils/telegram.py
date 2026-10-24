import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from twisted.internet import defer, threads
from twisted.python import log

from buildbot.process.results import SUCCESS, WARNINGS, FAILURE, EXCEPTION, CANCELLED
from buildbot.reporters.base import ReporterBase
from buildbot.reporters.generators.build import BuildStatusGenerator
from buildbot.reporters.message import MessageFormatterEmpty


def read_settings(path):
    try:
        raw = Path(path).read_text()
        if not raw.strip():
            return None
        settings = json.loads(raw)
        if not isinstance(settings, dict) or set(settings) - {
            'bot_token', 'chat_id', 'proxy', 'message_thread_id'
        }:
            raise ValueError()
        token = settings.get('bot_token')
        chat = settings.get('chat_id')
        if not isinstance(token, str) or not re.fullmatch(r'[0-9]+:[A-Za-z0-9_-]+', token):
            raise ValueError()
        if isinstance(chat, bool) or not isinstance(chat, (str, int)) or not str(chat).strip():
            raise ValueError()
        proxy = settings.get('proxy', '')
        if not isinstance(proxy, str) or any(ord(c) < 32 for c in proxy):
            raise ValueError()
        if proxy:
            parsed = urlsplit(proxy)
            if (parsed.scheme not in ('http', 'https', 'socks5', 'socks5h')
                    or not parsed.hostname or not parsed.port
                    or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
                raise ValueError()
        thread = settings.get('message_thread_id')
        if thread is not None and (type(thread) is not int or thread <= 0):
            raise ValueError()
        return settings
    except (OSError, UnicodeError, ValueError, TypeError):
        raise ValueError('Invalid Telegram configuration: check the private JSON file') from None


def send_message(config_file, text):
    try:
        settings = read_settings(config_file)
        if settings is None:
            return False
        payload = {
            'chat_id': settings['chat_id'],
            'text': text[:4000],
            'link_preview_options': {'is_disabled': True},
        }
        if 'message_thread_id' in settings:
            payload['message_thread_id'] = settings['message_thread_id']
        options = {
            'url': 'https://api.telegram.org/bot' + settings['bot_token'] + '/sendMessage',
            'proxy': settings.get('proxy', ''),
            'noproxy': '',
            'proto': '=https',
            'connect-timeout': '10',
            'max-time': '30',
            'max-filesize': '65536',
            'header': 'Content-Type: application/json',
            'data-binary': json.dumps(payload, ensure_ascii=False),
        }
        curl_config = 'silent\nfail\n' + ''.join(
            key + ' = ' + json.dumps(value, ensure_ascii=False) + '\n'
            for key, value in options.items()
        )
        result = subprocess.run(
            ['curl', '--disable', '--config', '-'], input=curl_config,
            text=True, capture_output=True, timeout=35, check=False,
        )
        if result.returncode:
            return False
        response = json.loads(result.stdout)
        return isinstance(response, dict) and response.get('ok') is True
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return False


def build_message(build):
    bad_results = (FAILURE, EXCEPTION, CANCELLED)
    result = build['results']
    if result in (SUCCESS, WARNINGS):
        if (build.get('prev_build') or {}).get('results') not in bad_results:
            return None
        status = 'recovered'
    elif result in bad_results:
        status = {FAILURE: 'failed', EXCEPTION: 'exception', CANCELLED: 'cancelled'}[result]
    else:
        return None
    lines = ['ScummVM iOS5: ' + status,
             build['builder']['name'] + ' #' + str(build['number'])]
    failed = [step['name'] for step in build.get('steps', [])
              if step.get('results') in bad_results]
    if failed:
        lines.append('Step: ' + ', '.join(failed)[:500])
    revision = build.get('properties', {}).get('got_revision', [None])[0]
    if isinstance(revision, str) and re.fullmatch(r'[0-9a-fA-F]{7,64}', revision):
        lines.append('Revision: ' + revision[:12])
    lines.append(build['url'])
    return '\n'.join(lines)


class TelegramStatusPush(ReporterBase):
    name = 'TelegramStatusPush'
    compare_attrs = (*ReporterBase.compare_attrs, 'config_file')

    def _generators(self):
        return [BuildStatusGenerator(
            builders=['sync-ios5', 'fetch-master', 'master-ios5'],
            mode=('failing', 'exception', 'cancelled', 'change'),
            message_formatter=MessageFormatterEmpty(want_steps=True),
        )]

    def checkConfig(self, config_file):
        read_settings(config_file)
        super().checkConfig(generators=self._generators())

    @defer.inlineCallbacks
    def reconfigService(self, config_file):
        self.config_file = config_file
        yield super().reconfigService(generators=self._generators())

    @defer.inlineCallbacks
    def sendMessage(self, reports):
        for report in reports:
            for build in report['builds']:
                message = build_message(build)
                if message is not None:
                    delivered = yield threads.deferToThread(send_message, self.config_file, message)
                    if not delivered:
                        log.msg('Telegram notification failed; check configuration and connectivity')


if __name__ == '__main__':
    import os
    import sys
    path = os.environ.get('IOS5_TELEGRAM_CONFIG_FILE', '')
    if len(sys.argv) != 2 or sys.argv[1] != '--test' or not path:
        sys.exit('Usage: telegram.py --test with IOS5_TELEGRAM_CONFIG_FILE set')
    if not send_message(path, 'ScummVM iOS5: Telegram test notification'):
        sys.exit('Telegram test failed; check configuration and connectivity')
    print('Telegram test delivered')
