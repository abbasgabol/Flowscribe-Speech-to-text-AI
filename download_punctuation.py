"""Install only the quantized punctuation model and its vocabulary."""
from pathlib import Path
import shutil
import subprocess
import tarfile
from download_model import valid

ROOT = Path(__file__).parent / 'models'
FILES = {
    'model.int8.onnx': '9d611f445fe4a46186080fe161be6059d87d72eb88d3a8cb00c1a06e83a6067e',
    'bpe.vocab': 'e118b7ad88c54db562517df49e1cffd4836d166c34fb190fd311d7f34eb238f5',
}
ARCHIVE_HASH = '9f5e5a72c7d2829635bd074fce92b6bbd5b78da8a52e7ad8ed1be933f366b99d'

if __name__ == '__main__':
    folder = ROOT / 'punctuation'
    folder.mkdir(parents=True, exist_ok=True)
    if not all(valid(folder / name, digest) for name, digest in FILES.items()):
        archive = ROOT / 'punctuation.tar.bz2'
        if not valid(archive, ARCHIVE_HASH):
            curl = shutil.which('curl.exe')
            if not curl:
                raise RuntimeError('Windows curl.exe is required for setup.')
            subprocess.run([curl, '-L', '--fail', '--retry', '2', '--max-time', '600',
                '--output', str(archive),
                'https://github.com/k2-fsa/sherpa-onnx/releases/download/punctuation-models/'
                'sherpa-onnx-online-punct-en-2024-08-06.tar.bz2'], check=True)
            if not valid(archive, ARCHIVE_HASH):
                raise RuntimeError('Punctuation archive checksum failed.')
        with tarfile.open(archive) as package:
            for member in package.getmembers():
                name = Path(member.name).name
                if member.isfile() and name in FILES:
                    temporary = folder / (name + '.download')
                    with package.extractfile(member) as source, temporary.open('wb') as destination:
                        shutil.copyfileobj(source, destination)
                    if not valid(temporary, FILES[name]):
                        raise RuntimeError(f'Punctuation checksum failed: {name}')
                    temporary.replace(folder / name)
    if not all(valid(folder / name, digest) for name, digest in FILES.items()):
        raise RuntimeError('Punctuation package is incomplete.')
    print('Punctuation model verified. Offline punctuation is ready.')
