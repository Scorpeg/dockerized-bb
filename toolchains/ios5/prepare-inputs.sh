#!/usr/bin/env bash
set -euo pipefail
[[ $# == 2 ]] || { echo 'Usage: prepare-inputs.sh SDK_ZIP TOOLCHAIN_TAR_XZ' >&2; exit 2; }
context=$(cd "$(dirname "$0")" && pwd -P)
sdk=$(realpath "$1")
toolchain=$(realpath "$2")
echo "451c6ca546c6a9f7bd3257a70547c4b66b9bda420ba11ecc0801424615c7aa92  $sdk" | sha256sum -c -
echo "a72a7a577e2fbe2838b6b5e9c72034fa7d114af96f0e1d4b016f18730ce4056e  $toolchain" | sha256sum -c -
mkdir -p "$context/local"
if [[ $sdk != "$context/local/iPhoneOS5.1.sdk.zip" ]]; then cp "$sdk" "$context/local/iPhoneOS5.1.sdk.zip"; fi
if [[ $toolchain != "$context/local/iOSToolchain-x86_64.tar.xz" ]]; then cp "$toolchain" "$context/local/iOSToolchain-x86_64.tar.xz"; fi
docker build --target fetch-tools -t ios5-fetch-tools "$context"
docker run --rm --user "$(id -u):$(id -g)" -v "$context:/opt/ios5" -w /opt/ios5 ios5-fetch-tools bash -c 'python3 scripts/full_deps.py fetch && python3 scripts/fetch-ui.py'
