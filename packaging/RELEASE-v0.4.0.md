# Local Dictation 0.4.0 beta

A smaller offline Windows installer, with base.en speech recognition and local punctuation included. No account, API key, Python installation, or setup-time model download is needed.

- Removes the bundled small.en model from the download.
- Trims unused Python packaging components while retaining required inference libraries and licenses.
- Defaults new installations to base.en; falls back to base.en when a saved model is absent.
- Shows only installed speech models in Preferences.
- Refreshes the managed runtime on upgrades while preserving model storage and user corrections.
- Enforces a download budget below 400,000,000 bytes during builds.

Hold Win + Alt to speak, then release to insert text. Recognition and punctuation settings are unchanged. Compared with small.en, base.en trades some recognition accuracy for lower resource use; this is not an accuracy-equivalent replacement for every recording.

Windows 10/11 x64. Existing optional small.en files are not deleted on upgrade. Uninstall/reinstall is not necessary.

Download: **219.9 MB** (219,873,359 bytes), about 67% smaller than the original 0.3.0 installer.

SHA-256: `31e310bdd8a33ecc76d48b351d4aff5e433b1067648cc3cb2971586188a6731c`
