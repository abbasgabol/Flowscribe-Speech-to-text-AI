"""Preserve inference/provider DLLs and redistribution notices, not tooling."""
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

binaries = collect_dynamic_libs('onnxruntime')
datas = collect_data_files('onnxruntime', includes=['LICENSE', 'ThirdPartyNotices.txt'])
