"""Install the optional pinned small.en speech model."""
import _bootstrap  # Allow direct execution from any working directory.
import hashlib
from pathlib import Path
import shutil
import subprocess

REVISION = 'd1d751a5f8271d482d14ca55d9e2deeebbae577f'
FILES = {
    'config.json': ('git', 'ced3fd5bbb3e9f7664658065d2d36164712cf1d5'),
    'tokenizer.json': ('git', '15d7bdf9ba25718ca2504eec6a8f02bc55af0a6a'),
    'vocabulary.txt': ('git', 'ee695b8d3e3c10d488304e04468efec4ca27554a'),
    'model.bin': ('sha256', '62b2a45b05ee59acb4a5341b33ee35e041395d378d418a18acfe4c9e768ee37a'),
}

def valid(path, kind, expected):
    if not path.is_file():
        return False
    digest = hashlib.sha1() if kind == 'git' else hashlib.sha256()
    if kind == 'git':
        digest.update(f'blob {path.stat().st_size}\0'.encode())
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            digest.update(chunk)
    return digest.hexdigest() == expected

if __name__ == '__main__':
    folder = Path(__file__).resolve().parents[1] / 'models' / 'small.en'
    folder.mkdir(parents=True, exist_ok=True)
    for name, (kind, digest) in FILES.items():
        destination = folder / name
        if valid(destination, kind, digest):
            continue
        temporary = folder / (name + '.download')
        if not valid(temporary, kind, digest):
            curl = shutil.which('curl.exe')
            if not curl:
                raise RuntimeError('Windows curl.exe is required.')
            subprocess.run([curl, '-L', '--fail', '--retry', '2', '--connect-timeout', '20',
                '--max-time', '900', '--continue-at', '-', '--output', str(temporary),
                f'https://huggingface.co/Systran/faster-whisper-small.en/resolve/{REVISION}/{name}'], check=True)
            if not valid(temporary, kind, digest):
                raise RuntimeError(f'Checksum failed: {name}')
        temporary.replace(destination)
    print('Accuracy model verified and ready.', flush=True)
