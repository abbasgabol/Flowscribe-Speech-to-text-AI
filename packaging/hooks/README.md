# Inference-only packaging hooks

These hooks replace blanket `--collect-all` collection. They apply only to the
frozen Windows application; the developer environment keeps all installed packages.
Model files, decoding settings, and numerical libraries are unchanged.

- `faster_whisper`: retain packaged Silero VAD data; normal analysis follows Python imports.
- `ctranslate2`: retain native inference libraries; conversion/spec tooling is excluded.
- `onnxruntime`: retain provider/runtime DLLs and license/third-party notices. Model
  conversion, quantization, and transformer tooling is excluded from the executable.
- `sherpa_onnx`: retain its Python extension (discovered by analysis) and adjacent
  ONNX Runtime DLL. The standalone C/C++ API DLLs, headers and import libraries
  are not used by this application's Python bindings.
- `PIL.Image`: retain ICO, PNG and BMP plugins needed by Windows tray serialization.
  The app does not expose arbitrary image import/export. Preserve these formats
  and add coverage before introducing new image features.

`hf_xet` is excluded: installed app inference uses explicit local model paths;
developer model downloads use the existing verified downloader scripts.

Do not remove FFmpeg DLLs based on their codec names. The current `avcodec` binary
imports video-encoder libraries even when the app decodes only audio. Likewise,
do not merge the separate ONNX Runtime binaries without ABI validation.

On dependency upgrades, inspect binary dependencies and rerun both-model frozen
checks, icon serialization, silence detection and clean installation. A successful
PyInstaller build alone does not validate a hook.
