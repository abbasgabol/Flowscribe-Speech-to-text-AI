"""Build a clean, reproducible source/setup ZIP; never include personal runtime data."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
FILES = [
    'app.py', 'desktop_ui.py', 'launch.py', 'app_paths.py', 'packaged_check.py', 'win_input.py', 'memory_stats.py',
    'personalization.py', 'punctuation.py', 'speech_settings.py', 'text_spacing.py',
    'time_formatting.py', 'download_model.py', 'download_accuracy_model.py',
    'download_punctuation.py', 'requirements.txt', 'requirements-lock.txt',
    'Setup.cmd', 'Install.ps1', 'setup.bat', 'setup_accuracy.bat', 'run.bat',
    'START-HERE.txt', 'README.md', 'ARCHITECTURE.md', 'LICENSE',
    'THIRD-PARTY-NOTICES.md', 'app.ico', 'build_release.py',
    'tests/test_hold_to_talk.py', 'tests/test_personalization.py',
    'tests/test_punctuation.py', 'tests/test_text_spacing.py',
    'tests/test_time_formatting.py', 'tests/test_win_input.py',
    'tests/test_app_paths.py',
]

def build():
    destination = ROOT / 'website' / 'dist' / 'downloads'
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / 'Local-Dictation-Source-0.3.0.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name in FILES:
            data = (ROOT / name).read_bytes()
            entry = zipfile.ZipInfo('Local-Dictation/' + name, date_time=(2026, 11, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(entry, data)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (destination / 'SOURCE-SHA256SUMS.txt').write_text(f'{digest}  {archive.name}\n', encoding='ascii')
    release = {'version': '0.3.0', 'file': archive.name, 'bytes': archive.stat().st_size,
               'sha256': digest, 'type': 'source-setup-zip'}
    (destination / 'source-release.json').write_text(json.dumps(release, indent=2) + '\n', encoding='utf-8')
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        assert len(bundle.namelist()) == len(FILES)
    print(json.dumps(release, indent=2))

if __name__ == '__main__':
    build()
