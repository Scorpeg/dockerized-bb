import os
from pathlib import Path
import shutil
import subprocess
import sys

repo = Path(os.environ['IOS5_BUILDBOT_ROOT'])
root = Path(os.environ.get('IOS5_STATE_DIR', str(repo / '.build/ios5-web')))
data = Path(os.environ.get('IOS5_DATA_DIR', str(repo / 'buildbot-data')))
if sys.argv[1:] not in ([], ['--check']):
    raise SystemExit('Usage: web-master.py [--check]')
if not os.environ.get('IOS5_REPOSITORY') and not os.environ.get('IOS5_LOCAL_SOURCE'):
    raise SystemExit('Set IOS5_REPOSITORY to your fork URL')
jobs = int(os.environ.get('IOS5_JOBS', '6'))
if jobs < 1:
    raise SystemExit('IOS5_JOBS must be positive')
data.mkdir(parents=True, exist_ok=True)
config = root / 'config'
shutil.copytree(repo / 'buildbot-config', config, dirs_exist_ok=True)
text = (config / 'config.py.example').read_text()
text += f'\ndata_dir = {str(data)!r}\n'
text += 'daily_builds_dir = os.path.join(data_dir, "packages", "dailybuilds")\n'
public_url = os.environ.get('IOS5_PUBLIC_URL', 'http://127.0.0.1:8010/').rstrip('/') + '/'
listen_address = os.environ.get('IOS5_LISTEN_ADDRESS', '127.0.0.1')
text += f'buildbot_url = {public_url!r}\n'
text += f'www_port = ({listen_address!r}, 8010)\n'
text += 'title = "ScummVM iOS5"\ngithub_avatars = False\n'
text += f'max_jobs = {jobs}\n'
text += 'serve_daily_builds = True\n'
if os.environ.get('IOS5_REPOSITORY'):
    text += f'ios5_repository = {os.environ["IOS5_REPOSITORY"]!r}\n'
    text += 'ios5_giturl = ios5_repository\n'
text += 'daily_builds_url = buildbot_url + "plugins/wsgi_dashboards/dailybuilds/packages/"\n'
source = os.environ.get('IOS5_LOCAL_SOURCE')
sync_setting = os.environ.get('IOS5_DAILY_SYNC', '0' if source else '1')
if sync_setting not in ('0', '1'):
    raise SystemExit('IOS5_DAILY_SYNC must be 0 or 1')
daily_sync = sync_setting == '1'
if daily_sync:
    token = os.environ.get('IOS5_GIT_TOKEN_FILE')
    if not token or not Path(token).read_bytes().strip():
        raise SystemExit('Set IOS5_GIT_TOKEN_FILE to a readable, nonempty Git token file')
if source and daily_sync:
    raise SystemExit('Daily sync requires the published fork, not IOS5_LOCAL_SOURCE')
text += f'ios5_daily_sync = {daily_sync!r}\n'
text += f'ios5_sync_script = {str(repo / "scripts/sync-ios5.sh")!r}\n'
if source:
    text += f'ios5_repository = {Path(source).as_uri()!r}\nios5_giturl = ios5_repository\n'
    text += 'ios5_stable_seconds = 10\n'
(config / 'config.py').write_text(text)
master_cfg = config / 'master.cfg'
text = master_cfg.read_text().replace('import workers, builds, platforms, ui', 'import workers, builds, platforms, ui\nui.www["authz"] = ui.util.Authz(allowRules=[ui.util.AnyControlEndpointMatcher(role="admin")])')
master_cfg.write_text(text)
master = root / 'master'
cli = str(Path(sys.executable).with_name('buildbot'))
if not (master / 'buildbot.tac').exists():
    subprocess.run([cli, 'create-master', '--relocatable', '--no-logrotate', '--config', '../config/master.cfg', str(master)], check=True)
subprocess.run([cli, 'checkconfig', str(master)], check=True)
if '--check' not in sys.argv:
    os.chdir(master)
    twistd = str(Path(sys.executable).with_name('twistd'))
    os.execv(twistd, [twistd, '--no_save', '--nodaemon', '--logfile=-', '--pidfile=', '--python=buildbot.tac'])
