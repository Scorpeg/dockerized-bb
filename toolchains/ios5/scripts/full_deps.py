#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
archives = root / 'vendor/full-archives'
lock = json.loads((root / 'full-dependencies.lock.json').read_text())
action = sys.argv[1] if len(sys.argv) == 2 else ''
assert action in ('verify', 'fetch'), 'Usage: full_deps.py {verify|fetch}'
archives.mkdir(parents=True, exist_ok=True)
for name, expected in lock['sha256'].items():
    path = archives / name
    if path.exists():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, 'Cached archive changed: ' + name
if action == 'fetch':
    for name, package in lock['packages'].items():
        files = [filename for filename in lock['sha256'] if filename.startswith(name + '_')]
        if all((archives / filename).exists() for filename in files):
            continue
        subprocess.run(['apt-get', 'source', '--download-only', '--only-source', '-y', name + '=' + package['version']], cwd=archives, check=True)
    for name, package in lock['extra'].items():
        filename = package.get('archive', 'cacert.pem' if name == 'ca_bundle' else '')
        assert filename in lock['sha256'], name
        path = archives / filename
        if path.exists():
            continue
        temporary = path.with_name(path.name + '.download')
        subprocess.run(['curl', '-fL', '--retry', '3', package['url'], '-o', str(temporary)], check=True)
        assert hashlib.sha256(temporary.read_bytes()).hexdigest() == lock['sha256'][filename], 'Downloaded revision differs from lock: ' + filename
        temporary.replace(path)
for name, expected in lock['sha256'].items():
    assert hashlib.sha256((archives / name).read_bytes()).hexdigest() == expected, name
print('PASS: dependency archive lock', len(lock['sha256']), 'files')
