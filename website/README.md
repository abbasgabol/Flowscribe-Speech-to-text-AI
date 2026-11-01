# Local Dictation website

Static HTML, CSS, and JavaScript. No build tool or external font/image dependencies.

From the application root, build the release with:

    .venv\Scripts\python.exe build_release.py

Preview with:

    .venv\Scripts\python.exe -m http.server 8765 --bind 127.0.0.1 --directory website/dist

The download buttons reference the actual ZIP in `dist/downloads`.
`SHA256SUMS.txt` and `release.json` are regenerated alongside the ZIP. Keep all three
together when updating a release. `desktop-preview.png` is captured from the app
with illustrative transcript content, not a claimed recognition result.

The `.openai/hosting.json` file records the private Sites project registration.
Publication is pending explicit approval: automatic approval review rejected
uploading this project to Sites. No website source or release ZIP was uploaded.

Local validation: desktop 1440 px and mobile 390/320 px, no horizontal overflow;
preview images loaded; example playback completed; download returned a valid ZIP.
No cloud transcription, accounts, analytics, or microphone access are present.
