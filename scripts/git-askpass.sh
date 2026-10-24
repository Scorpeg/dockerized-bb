#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
    *Username*) printf '%s\n' x-access-token ;;
    *Password*) cat "${IOS5_GIT_TOKEN_FILE:?}" ;;
    *) exit 1 ;;
esac
