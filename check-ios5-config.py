import os
from pathlib import Path
import shutil
import subprocess
import docker

root = Path('/check')
config = root/'config'
shutil.copytree('/bb/buildbot-config', config, dirs_exist_ok=True)
text = (config/'config.py.example').read_text()
text += '\ndocker_workers_net = "ios5-config-check"\ndata_dir = "/check/data"\nbuildbot_url = "http://127.0.0.1:8010/"\n'
(config/'config.py').write_text(text)
client = docker.from_env()
existing = bool(client.networks.list(names=['ios5-config-check']))
try:
    master = root/'master'
    if not (master/'buildbot.tac').exists():
        subprocess.run(['/check/venv/bin/buildbot', 'create-master', '--config', '../config/master.cfg', str(master)], check=True)
    subprocess.run(['/check/venv/bin/buildbot', 'checkconfig', str(master)], check=True)
    print('PASS: actual Buildbot 4.3.0 master configuration')
finally:
    if not existing:
        for network in client.networks.list(names=['ios5-config-check']):
            if network.name == 'ios5-config-check': network.remove()
