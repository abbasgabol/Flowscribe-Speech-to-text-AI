# Contributing

Develop on Windows 10/11 x64 with Python 3.10 or 3.11. Run `scripts\setup.bat`
to create `.venv` and download dependencies and lightweight models. Keep personal
audio and corrections out of commits.

## Application changes

Runtime modules belong in `local_dictation/`, using package-qualified imports.
Start the app with `run.bat` or `.venv\Scripts\python.exe -m local_dictation`.
Use `local_dictation.app_paths` for resources and preserve both source and frozen
application behavior. Developer tools belong in `scripts/`.

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe scripts/verify.py base.en
```

Unit tests require dependencies but no models. Integration checks require models
and a Windows desktop. Locally available synthetic WAV files under `tests/` enable
additional recognition checks. The verifier does not record the microphone.
Report skipped checks when submitting a change.

## Builds and releases

Install `packaging/build-requirements.txt`, place Inno Setup in `tools/InnoSetup`,
and download base.en and punctuation. Build into a test directory to preserve published files:

```powershell
.\.venv\Scripts\python.exe scripts/build_installer.py --output-dir qa/release-check
.\.venv\Scripts\python.exe scripts/build_release.py --output-dir qa/source-check
```

Without `--output-dir`, builds write to `website/dist/downloads`. Test installation,
launch, and uninstallation before publishing. Follow [the release checklist](packaging/PUBLISHING.md).
Do not replace published binaries during unrelated refactoring. The EXE is ignored
by Git and must be uploaded as a GitHub Release asset.

## Pull requests

Explain the behavior change, its purpose, and checks performed. Add screenshots
for UI changes. Keep changes focused and update documentation when commands,
paths, or behavior change. Preserve the website's `website/dist` deployment path.
