#!/usr/bin/env bash
set -euo pipefail
PORT_ROOT=$(cd "$(dirname "$0")/.." && pwd -P)
mode=${1:-ios}
case "$mode" in
 ios)
  source "$PORT_ROOT/scripts/env.sh"
  png_cc="$PORT_ROOT/scripts/cc"
  png_ar="$IOS_TOOLCHAIN_BIN/ar"
  png_ranlib="$IOS_TOOLCHAIN_BIN/ranlib"
  ;;
 host)
  png_cc=${HOST_CC:-cc}
  png_ar=ar
  png_ranlib=ranlib
  ;;
 *) echo 'Usage: build_png.sh [ios|host]' >&2; exit 2 ;;
esac
source_dir="$PORT_ROOT/vendor/libpng"
output_dir="$PORT_ROOT/build/png-$mode"

python3 - "$PORT_ROOT/vendor" <<'CHECK'
from pathlib import Path
import hashlib, json, sys
root = Path(sys.argv[1])
lock = json.loads((root / 'libpng.lock.json').read_text())
assert hashlib.sha256((root / 'libpng.SHA256SUMS').read_bytes()).hexdigest() == lock['manifest_sha256']
CHECK
(cd "$source_dir" && sha256sum --check --status ../libpng.SHA256SUMS)
mkdir -p "$output_dir/include" "$output_dir/lib" "$output_dir/obj"
cp "$source_dir/png.h" "$source_dir/pngconf.h" "$output_dir/include/"
cp "$source_dir/scripts/pnglibconf.h.prebuilt" "$output_dir/include/pnglibconf.h"
sources=(png pngerror pngget pngmem pngpread pngread pngrio pngrtran pngrutil pngset pngtrans pngwio pngwrite pngwtran pngwutil)
objects=()
for name in "${sources[@]}"; do
 "$png_cc" -O2 -fvisibility=hidden -DPNG_ARM_NEON_OPT=0 -DPNG_INTEL_SSE_OPT=0 \
  -I"$output_dir/include" -I"$source_dir" -c "$source_dir/$name.c" -o "$output_dir/obj/$name.o"
 objects+=("$output_dir/obj/$name.o")
done
"$png_ar" rcs "$output_dir/lib/libpng.a" "${objects[@]}"
"$png_ranlib" "$output_dir/lib/libpng.a"
echo "PASS: pinned libpng 1.6.59 built statically for $mode"
