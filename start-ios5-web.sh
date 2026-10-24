#!/usr/bin/env bash
set -euo pipefail
[[ $# == 1 ]] || exit 2
repo=$(cd "$(dirname "$0")" && pwd -P)
name=scummvm-ios5-buildbot-web
case "$1" in
 stop) exec docker stop "$name" ;;
 status)
  docker ps -a --filter "name=^/$name$" --format '{{.Names}} {{.Status}}'
  curl --fail --silent http://127.0.0.1:8010/api/v2/builds?limit=5
  ;;
 start)
  if docker container inspect "$name" >/dev/null 2>&1; then
   docker start "$name"
  else
   data=${IOS5_DATA_DIR:-$repo/buildbot-data}
   mkdir -p "$repo/.build/ios5-web" "$data"
   data=$(cd "$data" && pwd -P)
   mounts=()
   source_mounts=''
   source_repository=${IOS5_REPOSITORY:-}
   if [[ -z ${IOS5_LOCAL_SOURCE:-} && -z $source_repository ]]; then
    echo 'Set IOS5_REPOSITORY to your fork URL' >&2
    exit 1
   fi
   if [[ -n ${IOS5_LOCAL_SOURCE:-} ]]; then
    source=$(cd "$IOS5_LOCAL_SOURCE" && pwd -P)
    common=$(git -C "$source" rev-parse --path-format=absolute --git-common-dir)
    mounts+=(-v "$source:$source:ro" -v "$common:$common:ro")
    source_mounts=$(printf '%s\n' "$source:$source:ro" "$common:$common:ro")
    mkdir -p "$data/pollers/master/objects/info" "$data/src"
    printf '%s\n' "$common/objects" > "$data/pollers/master/objects/info/alternates"
    if [[ ! -e $data/src/master ]]; then
     git clone --shared --branch ios5 "$source" "$data/src/master"
     git -C "$data/src/master" remote set-url origin "file://$source"
     printf '%s\n' "$common/objects" > "$data/src/master/.git/objects/info/alternates"
    fi
   fi
   docker run -d --name "$name" --restart unless-stopped --network host \
    --user "$(id -u):$(id -g)" --group-add "$(stat -c %g /var/run/docker.sock)" \
    --entrypoint /check/venv/bin/python \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$repo/.build/ios5-config-check:/check:ro" \
    -v "$repo:$repo" -v "$data:$data" "${mounts[@]}" \
    -e "IOS5_BUILDBOT_ROOT=$repo" -e "IOS5_DATA_DIR=$data" \
    -e "IOS5_REPOSITORY=$source_repository" \
    -e "IOS5_LOCAL_SOURCE=${IOS5_LOCAL_SOURCE:-}" -e "IOS5_SOURCE_MOUNTS=$source_mounts" \
    -w "$repo" masters/ios5 "$repo/scripts/web-master.py"
  fi
  for attempt in {1..30}; do
   if curl --fail --silent http://127.0.0.1:8010/api/v2/builders; then
    printf '\nBuildbot: http://127.0.0.1:8010/\n'
    exit 0
   fi
   sleep 1
  done
  docker logs --tail 60 "$name"
  exit 1
  ;;
 *) echo 'Usage: start-ios5-web.sh start|stop|status' >&2; exit 2 ;;
esac
