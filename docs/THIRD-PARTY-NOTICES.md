# Third-party software

Local Dictation's source license is in LICENSE. The Windows installer bundles
Python, dependencies, and pretrained model files, which remain subject to their
own licenses. License texts are included in the installed `licenses` folder.
The separate developer source ZIP does not contain runtime binaries or weights.

- Python: https://www.python.org/psf/license/
- Faster-Whisper: https://github.com/SYSTRAN/faster-whisper
- CTranslate2: https://github.com/OpenNMT/CTranslate2
- Whisper models: https://github.com/openai/whisper
- Converted English models: https://huggingface.co/Systran/faster-whisper-base.en
  and https://huggingface.co/Systran/faster-whisper-small.en
- Sherpa-ONNX and punctuation model: https://github.com/k2-fsa/sherpa-onnx
- Edge-Punct-Casing model (Apache 2.0): https://huggingface.co/frankyoujian/Edge-Punct-Casing
- SoundDevice / PortAudio: https://python-sounddevice.readthedocs.io/
- Pillow: https://python-pillow.github.io/
- NumPy: https://numpy.org/
- Pystray: https://github.com/moses-palmer/pystray
- Pyperclip: https://github.com/asweigart/pyperclip

The complete dependency versions are listed in requirements-lock.txt. Consult
each installed distribution's metadata for its license and transitive notices.
