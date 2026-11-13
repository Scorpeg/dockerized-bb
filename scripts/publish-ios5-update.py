import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tarfile
import zipfile


def output(*args):
    return subprocess.check_output(args, text=True).strip()


def publish(archive, destination, key, revision):
    if not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('Expected full source revision')
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination, prefix='.publish-') as temporary:
        temporary = Path(temporary)
        deb = temporary / 'package.deb'
        with zipfile.ZipFile(archive) as source:
            packages = [entry for entry in source.infolist() if entry.filename.endswith('.deb')]
            if len(packages) != 1 or not 0 < packages[0].file_size <= 512 * 1024 * 1024:
                raise ValueError('Expected one bounded iOS5 Debian package')
            with source.open(packages[0]) as src, deb.open('wb') as dst:
                shutil.copyfileobj(src, dst)
        if output('dpkg-deb', '-f', deb, 'Package') != 'org.scummvm.ios5':
            raise ValueError('Wrong update package')
        if output('dpkg-deb', '-f', deb, 'Architecture') != 'iphoneos-arm':
            raise ValueError('Wrong update architecture')
        version = output('dpkg-deb', '-f', deb, 'Version')
        if not re.fullmatch('[0-9A-Za-z.+:~\-]{1,128}', version):
            raise ValueError('Invalid package version')
        bundled_key = None
        has_helper = False
        with subprocess.Popen(['dpkg-deb', '--fsys-tarfile', str(deb)], stdout=subprocess.PIPE) as process:
            with tarfile.open(fileobj=process.stdout, mode='r|') as contents:
                for member in contents:
                    if member.name == './etc/scummvm-ios5-updater/public.pem':
                        if not member.isfile() or not 0 < member.size <= 16384:
                            raise ValueError('Invalid bundled update key')
                        bundled_key = contents.extractfile(member).read()
                    if member.name == './usr/libexec/scummvm-ios5-update':
                        has_helper = member.isfile() and member.uid == 0 and member.gid == 0 and member.mode == 0o4755
            process.stdout.close()
            if process.wait():
                raise ValueError('Cannot inspect update package contents')
        signing_public = subprocess.check_output(['openssl', 'pkey', '-in', str(key), '-pubout'])
        if not has_helper or bundled_key != signing_public:
            raise ValueError('Package lacks updater helper or contains a different update key')
        with deb.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        latest = destination / 'latest.update'
        if latest.exists():
            old = latest.read_text().splitlines()
            if len(old) != 8:
                raise ValueError('Invalid existing update manifest')
            comparison = subprocess.run(['dpkg', '--compare-versions', version, 'lt', old[3]]).returncode
            if comparison not in (0, 1):
                raise ValueError('Cannot compare update versions')
            if comparison == 0:
                raise ValueError('Refusing to publish an older update')
            if version == old[3] and digest != old[5]:
                raise ValueError('A changed package requires a new version')
        payload = '\n'.join(['SCUMMVM-IOS5-1', revision, version, str(deb.stat().st_size), digest, digest + '.deb', 'org.scummvm.ios5', '']).encode()
        unsigned = temporary / 'manifest'
        unsigned.write_bytes(payload)
        signature = subprocess.check_output(['openssl', 'dgst', '-sha256', '-sign', str(key), str(unsigned)])
        if len(signature) < 256 or len(signature) > 1024:
            raise ValueError('Expected RSA update signing key (2048 bits or larger)')
        signed = temporary / 'latest.update'
        signed.write_bytes(signature.hex().encode() + b'\n' + payload)
        signed.chmod(0o644)
        deb.chmod(0o644)
        os.replace(deb, destination / (digest + '.deb'))
        os.replace(signed, latest)
    archives = sorted(destination.glob('*.deb'), key=lambda path: path.stat().st_mtime, reverse=True)
    import time
    for old in archives[3:]:
        if old.name != digest + '.deb' and old.stat().st_mtime < time.time() - 86400:
            old.unlink()
    print('Published signed iOS5 update:', version, revision)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--key', type=Path, required=True)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    publish(args.archive, args.destination, args.key, args.revision)
