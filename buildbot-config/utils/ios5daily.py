from datetime import datetime
import os
import re
from zoneinfo import ZoneInfo

from twisted.internet import defer
from buildbot.plugins import schedulers, steps, util
from buildbot.process.logobserver import BufferLogObserver


class IOS5Nightly(schedulers.Nightly):
    def current_utc_offset(self, timestamp):
        return datetime.fromtimestamp(timestamp, ZoneInfo('Europe/Moscow')).utcoffset().total_seconds()


class SyncIOS5(steps.MasterShellCommand):
    def __init__(self, **kwargs):
        super().__init__(logEnviron=False, **kwargs)
        self.output = BufferLogObserver(wantStdout=True)
        self.addLogObserver('stdio', self.output)

    @defer.inlineCallbacks
    def run(self):
        result = yield super().run()
        if result != util.SUCCESS:
            return result
        revisions = re.findall(r'^IOS5_SYNC_REVISION=([0-9a-f]{40})$', self.output.getStdout(), re.MULTILINE)
        if len(revisions) != 1:
            yield self.addCompleteLog('sync-error', 'Sync completed without exactly one validated revision. No build scheduled.\n')
            return util.FAILURE
        self.setProperty('ios5_synced_revision', revisions[0], self.name)
        return util.SUCCESS


def get_schedulers(build):
    yield IOS5Nightly(name='sync-ios5-nightly', branch=build.branch,
                     builderNames=['sync-ios5'], hour=2, minute=15,
                     onlyIfChanged=False)
    yield schedulers.Triggerable(name='ios5-synced-fetch', builderNames=[build.names['bld-fetch']])


def get_builder(build, config, workers, lock):
    factory = util.BuildFactory()
    factory.addStep(SyncIOS5(
        name='sync master and rebase ios5',
        command=['bash', config.ios5_sync_script, '--push'],
        workdir=config.data_dir,
        env={
            'PATH': os.environ['PATH'],
            'HOME': os.environ.get('HOME', config.data_dir),
            'LC_ALL': 'C.UTF-8',
            'IOS5_REPOSITORY': build.giturl,
            'IOS5_BRANCH': build.branch,
            'IOS5_UPSTREAM': config.ios5_upstream,
            'IOS5_SYNC_CACHE': os.path.join(config.data_dir, 'sync-cache'),
            'IOS5_GIT_TOKEN_FILE': os.environ.get('IOS5_GIT_TOKEN_FILE', ''),
            'GIT_TERMINAL_PROMPT': '0',
        },
        haltOnFailure=True, runtime_timeout=3600))
    factory.addStep(steps.Trigger(
        name='queue fresh iOS5 build', schedulerNames=['ios5-synced-fetch'],
        sourceStamps=[{'revision': util.Property('ios5_synced_revision'),
                       'repository': build.giturl, 'branch': build.branch,
                       'project': build.name, 'codebase': ''}],
        set_properties={'clean': True, 'package': True},
        waitForFinish=False))
    return util.BuilderConfig(
        name='sync-ios5', workernames=workers.workers_by_type['fetcher'],
        workerbuilddir=os.path.join(config.data_dir, 'triggers', 'sync-ios5'), factory=factory,
        locks=[lock.access('counting')],
        tags=['sync', 'daily', build.name], project=build.name)
