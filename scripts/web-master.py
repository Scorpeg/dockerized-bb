import os
from pathlib import Path
import shutil
import subprocess

repo = Path(os.environ['IOS5_BUILDBOT_ROOT'])
root = repo / '.build/ios5-web'
data = Path(os.environ.get('IOS5_DATA_DIR', str(repo / 'buildbot-data')))
config = root / 'config'
shutil.copytree(repo / 'buildbot-config', config, dirs_exist_ok=True)
text = (config / 'config.py.example').read_text()
text += f'\ndata_dir = {str(data)!r}\n'
text += 'daily_builds_dir = os.path.join(data_dir, "packages", "dailybuilds")\n'
text += 'docker_workers_net = "ios5-web-workers"\n'
text += 'buildbot_url = "http://127.0.0.1:8010/"\n'
text += 'www_port = ("127.0.0.1", 8010)\n'
text += 'title = "ScummVM iOS5"\ngithub_avatars = False\nmax_jobs = 6\n'
text += 'serve_daily_builds = True\n'
if os.environ.get('IOS5_REPOSITORY'):
    text += f'ios5_repository = {os.environ["IOS5_REPOSITORY"]!r}\n'
    text += 'ios5_giturl = ios5_repository\n'
text += 'daily_builds_url = buildbot_url + "plugins/wsgi_dashboards/dailybuilds/packages/"\n'
source = os.environ.get('IOS5_LOCAL_SOURCE')
if source:
    text += f'ios5_repository = {Path(source).as_uri()!r}\nios5_giturl = ios5_repository\n'
    text += f'ios5_source_mounts = {os.environ["IOS5_SOURCE_MOUNTS"].splitlines()!r}\n'
    text += 'ios5_stable_seconds = 10\n'
(config / 'config.py').write_text(text)
master_cfg = config / 'master.cfg'
text = master_cfg.read_text().replace('import workers, builds, platforms, ui', 'import workers, builds, platforms, ui\nui.www["authz"] = ui.util.Authz(allowRules=[ui.util.AnyControlEndpointMatcher(role="admin")])')
master_cfg.write_text(text)
master = root / 'master'
cli = '/check/venv/bin/buildbot'
if not (master / 'buildbot.tac').exists():
    subprocess.run([cli, 'create-master', '--config', '../config/master.cfg', str(master)], check=True)
subprocess.run([cli, 'checkconfig', str(master)], check=True)
os.execv(cli, [cli, 'start', '--nodaemon', str(master)])
