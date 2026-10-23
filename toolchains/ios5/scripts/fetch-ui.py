import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

root = Path(__file__).resolve().parents[1]/'vendor'
for name in ['libpng', 'giflib', 'freetype']:
    lock = json.loads((root/(name+'.lock.json')).read_text())
    archive = root/'full-archives'/(name+'.source.tar')
    if not (root/name).exists():
        subprocess.run(['curl', '-fL', '--retry', '3', lock['archive_url'], '-o', str(archive)], check=True)
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == lock['archive_sha256'], name
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                parts = Path(member.name).parts[1:]
                if not parts: continue
                assert '..' not in parts and not Path(*parts).is_absolute()
                member.name = str(Path(*parts))
                tar.extract(member, root/name, filter='data')
        archive.unlink()
    assert hashlib.sha256((root/(name+'.SHA256SUMS')).read_bytes()).hexdigest() == lock['manifest_sha256']
    subprocess.run(['sha256sum', '--check', '--status', str(root/(name+'.SHA256SUMS'))], cwd=root/name, check=True)
    print('PASS: pinned UI dependency', name)
