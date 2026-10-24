#!/usr/bin/env bash
set -euo pipefail
[[ $# == 1 ]] || exit 2
cd "$(dirname "$0")"
case "$1" in
 start) exec docker compose up -d --build ;;
 stop) exec docker compose stop ;;
 status) exec docker compose ps ;;
 *) echo 'Usage: start-ios5-web.sh start|stop|status' >&2; exit 2 ;;
esac
