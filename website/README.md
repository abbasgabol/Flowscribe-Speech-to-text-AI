# Local Dictation website

Static HTML, CSS, and JavaScript. No build tool or external font/image dependencies.

From the application root, build the release with:

    .venv\Scripts\python.exe scripts/build_installer.py

Preview with:

    .venv\Scripts\python.exe -m http.server 8765 --bind 127.0.0.1 --directory website/dist

The primary download buttons point to a GitHub Release asset, hosted separately
from Vercel. The large EXE stays out of Git; deploying this repository alone will
not upload it. Follow `../packaging/PUBLISHING.md` to publish the matching release
before deploying link changes. `release.json` records the asset URL, size and hash.
The local source ZIP and checksum files remain ordinary static website assets.

The `.openai/hosting.json` file records the private Sites project registration.
Publication is pending explicit approval: automatic approval review rejected
uploading this project to Sites. No website source or installer was uploaded.

Layout validation: desktop 1440 px and mobile 390/320 px, no horizontal overflow;
preview images loaded; example playback completed; installer links, executable header, size, and SHA-256 were verified.
No cloud transcription, accounts, analytics, or microphone access are present.
