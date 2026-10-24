import os
from pathlib import Path
import sys
import uuid

if len(sys.argv) != 1:
    raise SystemExit('Usage: build-now.py')
directory = Path(os.environ.get('IOS5_DATA_DIR', '/data')) / 'manual-requests'
directory.mkdir(parents=True, exist_ok=True)
request = directory / (uuid.uuid4().hex + '.request')
with request.open('x'):
    pass
print('Queued sync-ios5 request ' + request.stem + '. Follow it in the Buildbot dashboard.')
