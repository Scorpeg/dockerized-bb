#!/usr/bin/env bash
set -euo pipefail
PORT_ROOT=$(cd "$(dirname "$0")/.." && pwd -P)
mode=${1:-ios}
extra_flags=()
case "$mode" in
 ios)
  source "$PORT_ROOT/scripts/env.sh"
  gif_cc="$PORT_ROOT/scripts/cc"
  gif_ar="$IOS_TOOLCHAIN_BIN/ar"
  gif_ranlib="$IOS_TOOLCHAIN_BIN/ranlib"
  ;;
 host)
  gif_cc=${HOST_CC:-cc}
  gif_ar=ar
  gif_ranlib=ranlib
  extra_flags=(-g -fsanitize=address,undefined -fno-omit-frame-pointer)
  ;;
 *) echo 'Usage: build_gif.sh [ios|host]' >&2; exit 2 ;;
esac
source_dir="$PORT_ROOT/vendor/giflib"
output_dir="$PORT_ROOT/build/gif-$mode"
python3 - "$PORT_ROOT/vendor" <<'CHECK'
from pathlib import Path
import hashlib, json, sys
root = Path(sys.argv[1])
lock = json.loads((root / 'giflib.lock.json').read_text())
assert hashlib.sha256((root / 'giflib.SHA256SUMS').read_bytes()).hexdigest() == lock['manifest_sha256']
CHECK
(cd "$source_dir" && sha256sum --check --status ../giflib.SHA256SUMS)
mkdir -p "$output_dir/include" "$output_dir/lib" "$output_dir/obj"
cp "$source_dir/gif_lib.h" "$output_dir/include/"
sources=(dgif_lib egif_lib gifalloc gif_err gif_font gif_hash openbsd-reallocarray quantize)
objects=()
for name in "${sources[@]}"; do
 "$gif_cc" -std=gnu99 -O2 -fvisibility=hidden "${extra_flags[@]}" -I"$source_dir" \
  -c "$source_dir/$name.c" -o "$output_dir/obj/$name.o"
 objects+=("$output_dir/obj/$name.o")
done
"$gif_ar" rcs "$output_dir/lib/libgif.a" "${objects[@]}"
"$gif_ranlib" "$output_dir/lib/libgif.a"
echo "PASS: pinned giflib 6.1.3 built statically for $mode"
