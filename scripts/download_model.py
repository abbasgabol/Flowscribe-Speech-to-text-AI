"""Download a pinned model and verify file integrity before activation."""
import _bootstrap  # Allow direct execution from any working directory.
import hashlib
from pathlib import Path
import shutil
import subprocess

REVISION = '3d3d5dee26484f91867d81cb899cfcf72b96be6c'
FILES = {
    'config.json': 'f3bc3821e9fc76a27bae538e11ae5b677dcdd352b4600429ce7951d398569aeb',
    'tokenizer.json': '929c5252409436dce1b38a75d1abbcb5e132d170d8e324e4e04ed915fa2d22df',
    'vocabulary.txt': 'ff77588746d3a2595d32ab5b69ffd7b95ce2441ac57533cb66fc3eb575a115cf',
    'model.bin': '2a166925539a16005f14ff328359f9b9adb9dc4fb631bb3b227526862e93e2ef',
}

def valid(path, expected):
    if not path.is_file():
        return False
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest() == expected

if __name__ == '__main__':
    folder = Path(__file__).resolve().parents[1] / 'models' / 'base.en'
    folder.mkdir(parents=True, exist_ok=True)
    curl = shutil.which('curl.exe')
    for filename, expected in FILES.items():
        destination = folder / filename
        if valid(destination, expected):
            print(f'{filename}: verified', flush=True)
            continue
        temporary = folder / (filename + '.download')
        if not valid(temporary, expected):
            if not curl:
                raise RuntimeError('Windows curl.exe is required for setup.')
            print(f'Downloading {filename}...', flush=True)
            subprocess.run([curl, '-L', '--fail', '--retry', '2', '--connect-timeout', '20',
                            '--max-time', '600', '--output', str(temporary),
                            f'https://huggingface.co/Systran/faster-whisper-base.en/resolve/{REVISION}/{filename}'], check=True)
            if not valid(temporary, expected):
                raise RuntimeError(f'Checksum failed for {filename}. Run setup again to retry.')
        temporary.replace(destination)
    print('Model ready. Dictation can run offline.', flush=True)
