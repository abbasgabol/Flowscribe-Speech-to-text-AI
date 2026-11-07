"""The Python extension uses ONNX Runtime; standalone C/C++ APIs are unused."""
from PyInstaller.utils.hooks import collect_dynamic_libs

binaries = collect_dynamic_libs('sherpa_onnx', search_patterns=['onnxruntime.dll'])
