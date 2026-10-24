#!/usr/bin/env bash
set -euo pipefail
[[ $# == 1 && ( $1 == --check || $1 == --push ) ]] || { echo 'Usage: sync-ios5.sh --check|--push' >&2; exit 2; }
mode=$1
fork=${IOS5_REPOSITORY:?Set IOS5_REPOSITORY to your fork URL}
branch=${IOS5_BRANCH:-ios5}
upstream=${IOS5_UPSTREAM:-https://github.com/scummvm/scummvm.git}
upstream_branch=${IOS5_UPSTREAM_BRANCH:-master}
master_branch=${IOS5_MASTER_BRANCH:-master}
git check-ref-format --branch "$branch" >/dev/null
git check-ref-format --branch "$upstream_branch" >/dev/null
git check-ref-format --branch "$master_branch" >/dev/null
[[ $branch != "$master_branch" ]] || { echo 'Port and master branches must differ' >&2; exit 2; }
export GIT_TERMINAL_PROMPT=0
if [[ -n ${IOS5_GIT_TOKEN_FILE:-} ]]; then
    [[ -s $IOS5_GIT_TOKEN_FILE ]] || { echo 'Missing or empty Git token file' >&2; exit 1; }
    script_dir=$(cd "$(dirname "$0")" && pwd -P)
    export GIT_ASKPASS="$script_dir/git-askpass.sh"
fi
work=$(mktemp -d "${TMPDIR:-/tmp}/ios5-sync.XXXXXXXX")
cache=${IOS5_SYNC_CACHE:-$work/cache}
mkdir -p "$cache"
cache=$(cd "$cache" && pwd -P)
exec 9>"$cache/sync.lock"
flock -n 9 || { echo 'Another iOS5 sync is running' >&2; rmdir "$work"; exit 1; }
gitdir="$cache/repository.git"
child=''
run_command() {
    setsid "$@" &
    child=$!
    local result=0
    wait "$child" || result=$?
    child=''
    return "$result"
}
cleanup() {
    result=$?
    trap - EXIT TERM INT
    if [[ -n $child ]]; then
        kill -TERM -- "-$child" 2>/dev/null || true
        sleep 0.2
        kill -KILL -- "-$child" 2>/dev/null || true
        wait "$child" 2>/dev/null || true
    fi
    git --git-dir="$gitdir" worktree remove --force "$work/src" >/dev/null 2>&1 || true
    rm -rf -- "$work"
    exit "$result"
}
trap cleanup EXIT
trap 'echo "Sync interrupted (TERM); stopping child processes" >&2; exit 143' TERM
trap 'echo "Sync interrupted (INT); stopping child processes" >&2; exit 130' INT
if [[ ! -d $gitdir ]]; then
    git -c init.defaultBranch=master init --bare "$gitdir"
fi
git --git-dir="$gitdir" config remote.origin.url "$fork"
git --git-dir="$gitdir" config remote.upstream.url "$upstream"
printf 'Fetching fork branches\n'
run_command git --git-dir="$gitdir" fetch --progress --no-tags origin \
    "+refs/heads/$branch:refs/remotes/origin/$branch" \
    "+refs/heads/$master_branch:refs/remotes/origin/$master_branch"
printf 'Fetching upstream master\n'
run_command git --git-dir="$gitdir" fetch --progress --no-tags upstream \
    "+refs/heads/$upstream_branch:refs/remotes/upstream/$upstream_branch"
before=$(git --git-dir="$gitdir" rev-parse "refs/remotes/origin/$branch")
master_before=$(git --git-dir="$gitdir" rev-parse "refs/remotes/origin/$master_branch")
upstream_revision=$(git --git-dir="$gitdir" rev-parse "refs/remotes/upstream/$upstream_branch")
if ! git --git-dir="$gitdir" merge-base --is-ancestor "$master_before" "$upstream_revision"; then
    echo "Fork $master_branch has commits absent from upstream; refusing to rewrite it" >&2
    exit 1
fi
run_command git --git-dir="$gitdir" worktree add --detach "$work/src" "$before"
committer_name=$(git --git-dir="$gitdir" show -s --format=%an "$before")
committer_email=$(git --git-dir="$gitdir" show -s --format=%ae "$before")
[[ -n $committer_name && -n $committer_email ]] || { echo 'Missing port author identity' >&2; exit 1; }
run_command git -C "$work/src" -c user.name="$committer_name" -c user.email="$committer_email" \
    rebase --no-rebase-merges --no-fork-point "$upstream_revision"
run_command python3 "$work/src/backends/platform/ios5/prepare.py" --source "$work/src" --output "$work/overrides"
after=$(git -C "$work/src" rev-parse HEAD)
[[ -z $(git -C "$work/src" rev-list --merges "$upstream_revision..HEAD") ]]
printf 'Fork master before: %s\nFork ios5 before: %s\nUpstream: %s\nValidated candidate: %s\n' "$master_before" "$before" "$upstream_revision" "$after"
if [[ $mode == --check ]]; then
    echo 'Check only: no branch was pushed.'
    exit 0
fi
if [[ $before != "$after" || $master_before != "$upstream_revision" ]]; then
    run_command git --git-dir="$gitdir" push --progress --atomic \
        "--force-with-lease=refs/heads/$master_branch:$master_before" \
        "--force-with-lease=refs/heads/$branch:$before" \
        origin "$upstream_revision:refs/heads/$master_branch" "$after:refs/heads/$branch"
else
    echo 'Already aligned: no push needed.'
fi
printf 'IOS5_SYNC_REVISION=%s\n' "$after"
