"""Build a standalone app then a native offline Windows setup wizard."""
import _bootstrap  # Allow direct execution from any working directory.
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def runtime_inventory(folder):
    """Record package growth with paths relative to the bundle, not the developer PC."""
    files = {p.relative_to(folder).as_posix(): p.stat().st_size
             for p in sorted(folder.rglob('*')) if p.is_file()}
    groups = {}
    for name, size in files.items():
        parts = name.split('/')
        group = '/'.join(parts[:2]) if parts[0] == '_internal' else parts[0]
        groups[group] = groups.get(group, 0) + size
    return {'bytes': sum(files.values()), 'groups': groups, 'files': files}

def build(output_dir=None):
    # Model hash checks use the same pinned manifests as the original downloaders.
    from download_model import FILES, valid
    from download_punctuation import FILES as PUNCTUATION
    for name, digest in FILES.items():
        assert valid(ROOT/'models/base.en'/name, digest), f'Invalid base model: {name}'
    for name, digest in PUNCTUATION.items():
        assert valid(ROOT/'models/punctuation'/name, digest), f'Invalid punctuation model: {name}'
    compiler = ROOT/'tools/InnoSetup/ISCC.exe'
    if not compiler.is_file():
        raise RuntimeError('Install Inno Setup in tools/InnoSetup before building.')
    licenses = ROOT/'packaging/licenses'
    licenses.mkdir(exist_ok=True)
    for name in ('Whisper', 'Edge-Punct-Casing', 'Sherpa-ONNX', 'CTranslate2', 'ONNXRuntime', 'Tokenizers'):
        if not (licenses/f'{name}-LICENSE.txt').is_file():
            raise RuntimeError(f'Missing required redistribution license: {name}')
    for dist in metadata.distributions():
        for item in dist.files or []:
            if any(token in item.name.lower() for token in ('license', 'copying', 'notice')) and '.dist-info' in str(item):
                source = Path(dist.locate_file(item))
                if source.is_file():
                    destination = licenses/dist.metadata['Name']/Path(str(item).split('.dist-info/',1)[-1])
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
    python_license = Path(sys.base_prefix)/'LICENSE.txt'
    if python_license.is_file(): shutil.copy2(python_license, licenses/'Python-LICENSE.txt')
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onedir', '--windowed',
        '--name', 'LocalDictation', '--icon', 'assets/app.ico', '--add-data', 'assets/app.ico;.',
        '--additional-hooks-dir', 'packaging/hooks',
        '--exclude-module', 'hf_xet',
        '--exclude-module', 'ctranslate2.converters',
        '--exclude-module', 'ctranslate2.specs',
        '--exclude-module', 'onnxruntime.tools',
        '--exclude-module', 'onnxruntime.transformers',
        '--exclude-module', 'onnxruntime.quantization',
        '--hidden-import', 'pystray._win32', '--paths', str(ROOT), 'packaging/entrypoint.py']
    subprocess.run(command, cwd=ROOT, check=True)
    destination = Path(output_dir).resolve() if output_dir else ROOT/'website/dist/downloads'
    destination.mkdir(parents=True, exist_ok=True)
    inventory = runtime_inventory(ROOT/'dist/LocalDictation')
    (destination/'runtime-inventory.json').write_text(json.dumps(inventory, indent=2)+'\n', encoding='utf-8')
    subprocess.run([str(compiler), '/O' + str(destination), 'packaging/LocalDictation.iss'], cwd=ROOT, check=True)
    installer = destination/'LocalDictation-Setup.exe'
    if installer.stat().st_size >= 400_000_000:
        raise RuntimeError('Installer exceeds the 400 MB download budget.')
    digest = hashlib.sha256(installer.read_bytes()).hexdigest()
    release = {'version':'0.4.0', 'file':installer.name, 'bytes':installer.stat().st_size,
               'sha256':digest, 'type':'windows-offline-installer',
               'download_url':'https://github.com/abbasgabol/Flowscribe-Speech-to-text-AI/releases/download/v0.4.0/LocalDictation-Setup.exe'}
    (destination/'release.json').write_text(json.dumps(release, indent=2)+'\n', encoding='utf-8')
    (destination/'SHA256SUMS.txt').write_text(f'{digest}  {installer.name}\n', encoding='ascii')
    print(json.dumps(release, indent=2))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir")
    build(parser.parse_args().output_dir)
