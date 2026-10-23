#!/usr/bin/env bash
set -euo pipefail
PORT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
if [[ -n ${IOS_TOOLCHAIN_BIN:-} && -n ${IOS_SDK_ROOT:-} ]]; then
 :
elif [[ -x /opt/toolchain/linux/iphone/bin/clang ]]; then
 export IOS_TOOLCHAIN_BIN=/opt/toolchain/linux/iphone/bin
 export IOS_SDK_ROOT=/opt/sdk/iPhoneOS5.1.sdk
else
 export IOS_TOOLCHAIN_BIN="$PORT_ROOT/../build/local-ios51/toolchain/linux/iphone/bin"
 export IOS_SDK_ROOT="$PORT_ROOT/../build/local-ios51/sdk/iPhoneOS5.1.sdk"
fi
export PATH="$IOS_TOOLCHAIN_BIN:$PATH"
export CC="$PORT_ROOT/scripts/cc" CXX="$PORT_ROOT/scripts/cxx"
export AR="$IOS_TOOLCHAIN_BIN/ar" RANLIB="$IOS_TOOLCHAIN_BIN/ranlib" NM="$IOS_TOOLCHAIN_BIN/nm"
export SDKROOT="$IOS_SDK_ROOT"
export SCUMMVM_BUILD_DIR=${SCUMMVM_BUILD_DIR:-"$PORT_ROOT/build"}
mkdir -p "$SCUMMVM_BUILD_DIR" "$PORT_ROOT/logs"
