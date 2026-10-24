import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def fetch(root):
    for name in ['libpng', 'giflib', 'freetype']:
        lock = json.loads((root / (name + '.lock.json')).read_text())
        manifest = root / (name + '.SHA256SUMS')
        if hashlib.sha256(manifest.read_bytes()).hexdigest() != lock['manifest_sha256']:
            raise ValueError('Manifest checksum mismatch: ' + name)
        destination = root / name

        def verified(path):
            if not path.is_dir():
                return False
            return subprocess.run(['sha256sum', '--check', '--status', str(manifest)], cwd=path).returncode == 0

        if not verified(destination):
            with tempfile.TemporaryDirectory(prefix=name + '-', dir=root) as temporary:
                work = Path(temporary)
                archive = work / 'source.tar'
                subprocess.run(['curl', '-fL', '--retry', '3', lock['archive_url'], '-o', str(archive)], check=True)
                if hashlib.sha256(archive.read_bytes()).hexdigest() != lock['archive_sha256']:
                    raise ValueError('Archive checksum mismatch: ' + name)
                extracted = work / 'source'
                extracted.mkdir()
                subprocess.run(['tar', '-xf', str(archive), '--strip-components=1', '-C', str(extracted)], check=True)
                if not verified(extracted):
                    raise ValueError('Extracted source checksum mismatch: ' + name)
                if destination.exists():
                    shutil.rmtree(destination)
                extracted.rename(destination)
        print('PASS: pinned UI dependency', name)


if __name__ == '__main__':
    fetch(Path(__file__).resolve().parents[1] / 'vendor')
