#!/usr/bin/env bash
set -euo pipefail
source /opt/ios5/scripts/env.sh
python3 "$PORT_ROOT/scripts/full_deps.py" verify
python3 "$PORT_ROOT/scripts/build_full_deps.py"
for library in png gif freetype; do
 bash "$PORT_ROOT/scripts/build_$library.sh" ios
 cp -a "$PORT_ROOT/build/$library-ios/include/." "$PORT_ROOT/build-full/deps/include/"
 cp -a "$PORT_ROOT/build/$library-ios/lib/." "$PORT_ROOT/build-full/deps/lib/"
done
cp "$PORT_ROOT/build/freetype-ios/bin/freetype-config" "$PORT_ROOT/build-full/deps/bin/"
python3 "$PORT_ROOT/scripts/dependency-manifest.py"
dpkg-query -W > "$PORT_ROOT/logs/host-packages.txt"
rm -rf "$PORT_ROOT/build-full/deps-work" "$PORT_ROOT/build"
