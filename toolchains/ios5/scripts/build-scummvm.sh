#!/usr/bin/env bash
set -euo pipefail
[[ $# == 2 ]] || { echo 'Usage: build-scummvm.sh SOURCE BUILD' >&2; exit 2; }
src=$(cd "$1" && pwd -P)
mkdir -p "$2"
cd "$2"
mkdir -p logs
trap 'result=$?; if (( result )); then echo "FAIL: $stage (exit $result)" >&2; tail -n 60 "logs/$stage.log" >&2; fi' EXIT
stage=configure
"$src/configure" --host=ios5 --enable-all-engines --enable-detection-full --enable-static \
 --with-staticlib-prefix="$PREFIX" --enable-mt32emu --enable-fluidsynth --enable-freetype2 --enable-png --enable-gif \
 --disable-opengl-game-classic --disable-discord --disable-retrowave --disable-tts \
 --disable-debug --disable-Werror --enable-release --enable-test-c++11 > logs/configure.log 2>&1
echo 'PASS: configure'
stage=build
make_args=(-j"${JOBS:-6}")
if [[ -n ${SCUMMVM_REVISION:-} ]]; then make_args+=(VER_REV="$SCUMMVM_REVISION"); fi
make "${make_args[@]}" > logs/build.log 2>&1
echo 'PASS: compile and link'
stage=package
make ios5deb > logs/package.log 2>&1
echo 'PASS: package and SDK audit'
sha256sum scummvm-*-ios5.deb
