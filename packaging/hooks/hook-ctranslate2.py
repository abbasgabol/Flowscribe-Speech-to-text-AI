"""Include the native inference runtime, without collecting conversion tooling."""
from PyInstaller.utils.hooks import collect_dynamic_libs

binaries = collect_dynamic_libs('ctranslate2')
