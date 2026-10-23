import hashlib
import json
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
prefix = root/'build-full/deps'
licenses = prefix/'share/ios5/licenses'
licenses.mkdir(parents=True, exist_ok=True)
for source in sorted((root/'build-full/deps-work').iterdir()):
    if not source.is_dir(): continue
    files = [p for p in source.iterdir() if p.is_file() and p.name.upper().startswith(('COPYING', 'LICENSE', 'COPYRIGHT'))]
    if (source/'debian/copyright').exists(): files.append(source/'debian/copyright')
    if not files: raise RuntimeError('Missing license: '+source.name)
    dest = licenses/source.name
    dest.mkdir(exist_ok=True)
    for file in files: shutil.copy2(file, dest/file.name)
for name, relative in [('libpng', 'LICENSE'), ('giflib', 'COPYING'), ('freetype', 'docs/FTL.TXT'), ('freetype', 'LICENSE.TXT')]:
    dest = licenses/name
    dest.mkdir(exist_ok=True)
    shutil.copy2(root/'vendor'/name/relative, dest/Path(relative).name)
shutil.copy2(root/'packaging/LICENSE-FreeType-bundled.txt', licenses)
for name in ['LICENSE', 'NOTICE.txt']:
    shutil.copy2(root/'build-full/deps-work/fluidsynth/gcem'/name, licenses/('gcem-'+name))
for file in [root/'full-dependencies.lock.json', *list((root/'vendor').glob('*.lock.json'))]:
    shutil.copy2(file, prefix/'share/ios5'/file.name)
shutil.copy2(root/'vendor/full-archives/cacert.pem', prefix/'share/ios5/cacert.pem')
manifest = {str(p.relative_to(prefix)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((prefix/'lib').glob('*.a'))}
(prefix/'share/ios5/libraries.sha256.json').write_text(json.dumps(manifest, indent=2)+'\n')
print('PASS: built static libraries and collected licenses:', len(manifest))
