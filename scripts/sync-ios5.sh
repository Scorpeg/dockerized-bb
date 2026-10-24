#!/usr/bin/env bash
set -euo pipefail
[[ $# == 1 && ( $1 == --check || $1 == --push ) ]] || { echo 'Usage: sync-ios5.sh --check|--push' >&2; exit 2; }
mode=$1
fork=${IOS5_REPOSITORY:?Set IOS5_REPOSITORY to your fork URL}
branch=${IOS5_BRANCH:-ios5}
upstream=${IOS5_UPSTREAM:-https://github.com/scummvm/scummvm.git}
upstream_branch=${IOS5_UPSTREAM_BRANCH:-master}
git check-ref-format --branch "$branch" >/dev/null
git check-ref-format --branch "$upstream_branch" >/dev/null
work=$(mktemp -d "${TMPDIR:-/tmp}/ios5-sync.XXXXXXXX")
trap 'rm -rf -- "$work"' EXIT
git init "$work/src"
git -C "$work/src" remote add origin "$fork"
git -C "$work/src" fetch --no-tags origin "refs/heads/$branch:refs/remotes/origin/$branch"
git -C "$work/src" checkout -b "$branch" "refs/remotes/origin/$branch"
git -C "$work/src" config user.name 'iOS5 upstream sync'
git -C "$work/src" config user.email 'ios5-sync@users.noreply.github.com'
git -C "$work/src" remote add upstream "$upstream"
git -C "$work/src" fetch --no-tags upstream "refs/heads/$upstream_branch:refs/remotes/upstream/$upstream_branch"
before=$(git -C "$work/src" rev-parse HEAD)
upstream_revision=$(git -C "$work/src" rev-parse "refs/remotes/upstream/$upstream_branch")
git -C "$work/src" merge -m "IOS: Merge upstream $upstream_branch into $branch" "refs/remotes/upstream/$upstream_branch"
python3 "$work/src/backends/platform/ios5/prepare.py" --source "$work/src" --output "$work/overrides"
after=$(git -C "$work/src" rev-parse HEAD)
printf 'Fork before: %s\nUpstream: %s\nValidated candidate: %s\n' "$before" "$upstream_revision" "$after"
if [[ $mode == --push && $before != "$after" ]]; then
 git -C "$work/src" push origin "HEAD:refs/heads/$branch"
elif [[ $mode == --check ]]; then
 echo 'Check only: no branch was pushed.'
else
 echo 'Already aligned: no push needed.'
fi
