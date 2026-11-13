import os
from pathlib import Path
import subprocess
from urllib.parse import urlsplit


def initialize(data, public_url):
    secret = Path(os.environ.get('IOS5_UPDATE_SIGNING_KEY_FILE', '/run/secrets/update_signing_key'))
    if not secret.is_file() or not secret.stat().st_size:
        return None
    url = urlsplit(public_url)
    if url.scheme != 'https' or not url.netloc or url.username or url.password or url.query or url.fragment:
        raise ValueError('Signed app updates require an HTTPS IOS5_PUBLIC_URL')
    config = data / 'updater-config'
    config.mkdir(parents=True, exist_ok=True)
    public = subprocess.check_output(['openssl', 'pkey', '-in', str(secret), '-pubout'])
    subprocess.run(['openssl', 'rsa', '-pubin', '-noout'], input=public, check=True, stdout=subprocess.DEVNULL)
    (config / 'public.pem').write_bytes(public)
    feed = public_url.rstrip('/') + '/plugins/wsgi_dashboards/dailybuilds/packages/master/updates/'
    (config / 'feed.url').write_text(feed + '\n')
    return {'key': str(secret), 'public_key': str(config / 'public.pem'), 'url': feed}
