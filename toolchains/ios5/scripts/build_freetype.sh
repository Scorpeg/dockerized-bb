#!/usr/bin/env bash
set -euo pipefail
PORT_ROOT=$(cd "$(dirname "$0")/.." && pwd -P)
mode=${1:-ios}
extra_flags=()
case "$mode" in
 ios)
  source "$PORT_ROOT/scripts/env.sh"
  ;;
 host)
  export CC=${HOST_CC:-cc} AR=ar RANLIB=ranlib NM=nm
  extra_flags=(-g -fsanitize=address,undefined -fno-omit-frame-pointer)
  ;;
 *) echo 'Usage: build_freetype.sh [ios|host]' >&2; exit 2 ;;
esac
python3 - "$PORT_ROOT/vendor" <<'CHECK'
from pathlib import Path
import hashlib, json, sys
root = Path(sys.argv[1])
lock = json.loads((root / 'freetype.lock.json').read_text())
assert hashlib.sha256((root / 'freetype.SHA256SUMS').read_bytes()).hexdigest() == lock['manifest_sha256']
CHECK
(cd "$PORT_ROOT/vendor/freetype" && sha256sum --check --status ../freetype.SHA256SUMS)
output_dir="$PORT_ROOT/build/freetype-$mode"
mkdir -p "$output_dir/obj" "$output_dir/include/freetype2" "$output_dir/lib" "$output_dir/bin"
cp -R "$PORT_ROOT/vendor/freetype/include/"* "$output_dir/include/freetype2/"
cat > "$output_dir/include/freetype2/freetype/config/ftmodule.h" <<'MODULES'
FT_USE_MODULE(FT_Module_Class, autofit_module_class)
FT_USE_MODULE(FT_Driver_ClassRec, tt_driver_class)
FT_USE_MODULE(FT_Driver_ClassRec, cff_driver_class)
FT_USE_MODULE(FT_Module_Class, psaux_module_class)
FT_USE_MODULE(FT_Module_Class, psnames_module_class)
FT_USE_MODULE(FT_Module_Class, pshinter_module_class)
FT_USE_MODULE(FT_Module_Class, sfnt_module_class)
FT_USE_MODULE(FT_Renderer_Class, ft_smooth_renderer_class)
FT_USE_MODULE(FT_Renderer_Class, ft_raster1_renderer_class)
MODULES
sources=(autofit/autofit base/ftbase base/ftsystem base/ftinit base/ftdebug
 base/ftbbox base/ftbdf base/ftbitmap base/ftcid base/ftfstype base/ftgasp
 base/ftglyph base/ftgxval base/ftmm base/ftotval base/ftpatent base/ftpfr
 base/ftstroke base/ftsynth base/fttype1 base/ftwinfnt cff/cff gzip/ftgzip
 psaux/psaux pshinter/pshinter psnames/psnames raster/raster sfnt/sfnt
 smooth/smooth truetype/truetype)
objects=()
for name in "${sources[@]}"; do
 object="$output_dir/obj/${name//\//_}.o"
 "$CC" -std=gnu99 -O2 -fvisibility=hidden "${extra_flags[@]}" -DFT2_BUILD_LIBRARY \
  -I"$output_dir/include/freetype2" -c "$PORT_ROOT/vendor/freetype/src/$name.c" -o "$object"
 objects+=("$object")
done
"$AR" rcs "$output_dir/lib/libfreetype.a" "${objects[@]}"
"$RANLIB" "$output_dir/lib/libfreetype.a"
cat > "$output_dir/bin/freetype-config" <<'CONFIG'
#!/usr/bin/env bash
prefix=$(cd "$(dirname "$0")/.." && pwd -P)
if [[ ${1:-} == --prefix=* ]]; then
 prefix=${1#--prefix=}
 shift
fi
case "$*" in
 --cflags) echo "-I$prefix/include/freetype2" ;;
 --libs|--static\ --libs) echo "-L$prefix/lib -lfreetype" ;;
 --ftversion) echo 2.15.0 ;;
 --prefix) echo "$prefix" ;;
 *) exit 2 ;;
esac
CONFIG
chmod 755 "$output_dir/bin/freetype-config"
echo "PASS: pinned FreeType 2.15.0 built statically for $mode"
