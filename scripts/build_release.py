"""Build a clean, reproducible source/setup ZIP; never include personal runtime data."""
import _bootstrap  # Allow direct execution from any working directory.
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
# Only source/configuration patterns are allowed; never include runtime data.
FILES = ['README.md', 'LICENSE', 'CONTRIBUTING.md', 'requirements.txt',
         'requirements-lock.txt', 'run.bat', 'assets/app.ico']
for pattern in ('local_dictation/*.py', 'scripts/*.py', 'scripts/*.bat',
                'scripts/*.cmd', 'scripts/*.ps1', 'scripts/*.mjs',
                'docs/*.md', 'docs/*.txt', 'tests/test_*.py',
                'packaging/*.py', 'packaging/*.iss', 'packaging/*.txt',
                'packaging/*.md', 'packaging/*.bmp', 'packaging/hooks/*.py',
                'packaging/hooks/*.md', 'packaging/licenses/*-LICENSE.txt'):
    FILES.extend(sorted(str(p.relative_to(ROOT)).replace('\\', '/') for p in ROOT.glob(pattern)))
FILES = sorted(set(FILES))

def build(output_dir=None):
    destination = Path(output_dir).resolve() if output_dir else ROOT / 'website' / 'dist' / 'downloads'
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / 'Local-Dictation-Source-0.4.0.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name in FILES:
            data = (ROOT / name).read_bytes()
            entry = zipfile.ZipInfo('Local-Dictation/' + name, date_time=(2026, 11, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(entry, data)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (destination / 'SOURCE-SHA256SUMS.txt').write_text(f'{digest}  {archive.name}\n', encoding='ascii')
    release = {'version': '0.4.0', 'file': archive.name, 'bytes': archive.stat().st_size,
               'sha256': digest, 'type': 'source-setup-zip'}
    (destination / 'source-release.json').write_text(json.dumps(release, indent=2) + '\n', encoding='utf-8')
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        assert len(bundle.namelist()) == len(FILES)
    print(json.dumps(release, indent=2))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir")
    build(parser.parse_args().output_dir)
