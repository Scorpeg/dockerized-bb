#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")" && pwd -P)
output="$root/.build/ios5-config-check"
mkdir -p "$output"
docker run --rm --user "$(id -u):$(id -g)" --group-add "$(stat -c %g /var/run/docker.sock)" --entrypoint bash \
 -v /var/run/docker.sock:/var/run/docker.sock -v "$root:/bb:ro" -v "$output:/check" -w /check workers/ios5 -c '
set -euo pipefail
python3 -m venv /check/venv
/check/venv/bin/pip install "buildbot[bundle]==4.3.0" "buildbot-wsgi-dashboards==4.3.0" "docker==7.2.0" "bottle==0.13.4" > /check/install.log 2>&1 || { tail -n 40 /check/install.log; exit 1; }
/check/venv/bin/pip freeze > /check/python-packages.txt
/check/venv/bin/python /bb/check-ios5-config.py 2>&1 | tee /check/check.log
'
