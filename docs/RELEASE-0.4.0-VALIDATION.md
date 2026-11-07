# Lightweight release 0.4.0

Built 2026-11-07. Download: 219,873,359 bytes (219.9 MB; 209.7 MiB), below the strict 400,000,000-byte budget.

Original 0.3.0 installer: 672,629,666 bytes. Reduction: 67.3%.

SHA-256: `31e310bdd8a33ecc76d48b351d4aff5e433b1067648cc3cb2971586188a6731c`

The release contains base.en and punctuation, with unchanged model files and decoding settings. It excludes small.en from the installer, not from existing installations or the developer checkout. Runtime packaging hooks retain inference dependencies and license notices while omitting unused tooling.

Artifacts: `qa/lightweight-release/LocalDictation-Setup.exe`, `release.json`, `SHA256SUMS.txt`, and source ZIP. These are local release artifacts. Website download links remain on the existing release until the new GitHub Release assets are uploaded, to avoid broken downloads.

Validation: all 31 unit tests pass; installer compiles and enforces the size budget. An isolated installer with a separate application ID passed clean installation, offline GUI/hotkey/transcription/punctuation smoke tests, and reinstall/upgrade. Upgrade removed an obsolete runtime marker and preserved a model-directory marker. Post-upgrade smoke tests passed. All six bundled model files match their original SHA-256 hashes, and small.en is absent. Tests ran on this PC, not a separate clean Windows machine.
