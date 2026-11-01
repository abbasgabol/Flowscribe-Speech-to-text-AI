# Local Dictation — Windows beta 0.3.0

## Install the downloadable release

Download `LocalDictation-Setup.exe` and open it. The wizard displays the MIT
license, lets you choose the destination drive/folder, select models and desktop
shortcuts, and launch the app afterward. Python, dependencies, and models are
bundled: no separate runtime installation or setup-time internet is needed.
Choose Lightweight for the smaller model or Complete to include Accuracy.

The app and models live in your chosen destination. Small settings and explicitly
saved corrections live in `%LOCALAPPDATA%\LocalDictation`, so installation in a
protected folder does not prevent saving preferences. Uninstall through Windows
Installed Apps. User preferences are deliberately preserved after removal.

The executable is unsigned. Windows may show an unknown-publisher warning; this
release does not claim code-signing or a verified publisher identity.

The interface has **Dictate** and **Preferences** views. The transcript, recording
button, and original-recognition viewer are in Dictate. Model choice, punctuation,
insertion options, and the personal dictionary are in Preferences.

## Building releases

Install the versions in `packaging/build-requirements.txt` in the project venv,
place Inno Setup 6 in `tools/InnoSetup`, and keep the verified model files under
`models`. Run `build_installer.py` to create the frozen app and native installer.
The script copies dependency licenses and requires the official model licenses
under `packaging/licenses`. The build uses an explicit model-file list, excluding
user preferences, dictionaries, audio, and model download caches.

`build_release.py` separately creates the developer source ZIP. It does not
replace the installer metadata. Website downloads live in `website/dist/downloads`;
`release.json` and `SHA256SUMS.txt` describe the installer, and `source-release.json`
describes the optional source download.

## Installer validation

The 0.3.0 installer was tested on the development Windows PC: welcome/license/
location/components/shortcut pages were inspected; license acceptance was required;
a Complete installation into a custom G: folder succeeded; the installed EXE loaded
its GUI and keyboard hook and transcribed synthetic audio with punctuation using its
bundled runtime. Automated source tests: 31 passed. A separate clean PC is not yet
validated. The release is unsigned. See `qa` logs locally for detailed test output.

## Developer setup and behavior

See [ARCHITECTURE.md](ARCHITECTURE.md) for the system diagram, component-to-logic table,
state transitions, resource choices, and validation boundaries.

Offline Windows English dictation with optional contextual punctuation and explicit
saved phrase corrections. No API key or grammar rewriting. Requires Python 3.10 or later.

1. Run `setup.bat` with internet access to install dependencies and both local models.
2. Open `run.bat`. Subsequent dictation runs offline.
3. Click in a text field so its typing cursor is active. **Hold Win + Alt** and speak.
4. Release either key to stop. Release both keys and keep that field active while transcription finishes.

Choose **Accuracy — small.en** for the larger English recognition model or
**Lightweight — base.en** for lower memory use and faster responses. The choice is saved
locally. Only one speech model is loaded at a time; switch while the app is idle.
On a fresh installation, run `setup_accuracy.bat` once to download the optional model
(about 484 MB) into this project's `models/small.en` directory. Downloads can resume.
When no preference exists, the app chooses Accuracy if its model is installed.

Explicit clock phrases are formatted automatically: `half past eight` → `8:30`,
`quarter past six` → `6:15`, `quarter to nine` → `8:45`. AM/PM is never guessed.
This step works with either speech model and with punctuation refinement disabled.
It cannot recover a time from unrelated misrecognized words such as `half car seat`;
that requires better recognition of the original audio. Numeric times are protected
from the punctuation model.

The recording button transcribes into the preview for testing. Copy text copies the
result manually. Automatic insertion preserves the clipboard. Esc cancels recording;
recordings stop at two minutes. Closing the window hides it in the system tray.
Use the tray menu to reopen it or quit.

Missing prose spaces such as `night?As`, `up?I`, and `up.So` are repaired independently
of the punctuation-model checkbox. Automatic insertion adds a trailing space by default
so consecutive dictations stay separated. Disable **Add a space after inserted dictation**
when editing inside existing text. Existing spaces/newlines and recognized technical
tokens (URLs, email addresses, decimals, code) are preserved. Ambiguous lowercase dotted
identifiers are left unchanged. Existing text already in another app is not rewritten.

**Improve punctuation** enables a small English punctuation model after recognition.
Disable it to use Whisper's punctuation alone. **View original transcript** shows what
Whisper recognized before saved corrections and refinement. Short sentences already
ending with punctuation and technical strings are preserved; longer prose is refined.
The small model can still miss boundaries or choose an unsuitable comma.

**Personal dictionary** lets you save and delete an exact misheard phrase and its desired
replacement. Only entries you save are stored in `personal_dictionary.json`; there is no
conversation history. Saved spellings are also short vocabulary hints for recognition.
Up to 200 entries are supported. This is personalization, not model-weight training or RL.
Use the checkbox to disable saved corrections for a recording.

The live memory display distinguishes physical RAM from private committed memory
(which Windows can keep in RAM or page out). It refreshes every three seconds.

Audio is held only in memory. The last transcript stays visible until replaced or the
app exits. No audio or transcript is uploaded. Setup downloads packages and model files;
runtime loads the local model directory only.

The CPU backend is faster-whisper, using INT8, beam size 5, and up to four threads.
A short punctuated transcript example supplies decoding context. Matrix prepacking is
disabled by default (`CT2_PACKED_GEMM=0`) after measuring a substantial reduction in
private committed memory on this laptop. The punctuation model uses one CPU thread.
The default Windows
microphone is used. Change it in Windows sound settings before starting a recording.
The shortcut uses a Windows keyboard hook to detect Win + Alt press and release.
Either left or right key works. Release both keys before the next recording.
Moving the mouse over a field does not focus it; click the intended field first.
This prototype has no startup-at-login setting or installer yet.

`requirements-lock.txt` records the tested Python dependencies used by setup.

Punctuation, accuracy and latency depend on speech, microphone and hardware. Automatic
list formatting and grammar cleanup are future work. Some custom editors and elevated
apps may reject Unicode insertion; use Copy text there. If you change windows during
processing, insertion is skipped. Moving the cursor within the same window is not detected.

## Manual acceptance check

Open Notepad, dictate a sentence and a question, and confirm punctuation and insertion.
Test silent recording, Esc cancellation, and switching windows while processing.
Disconnect internet and repeat. Confirm the tray menu reopens and quits the app.

Developer checks: `.venv\Scripts\python.exe -m unittest discover -s tests -v`.
`verify.py` checks model loading, the GUI, installed keyboard hook, insertion into its own
test editor and silent audio with Hugging Face offline mode enabled. If
`tests/sample.wav` exists, it also checks a spoken sentence and question.
It also exercises the full refinement pipeline and the new dictionary/memory controls.
`benchmark_memory.py` and `benchmark_decoding.py` record reproducible synthetic-speech
experiments; their JSON reports are ignored by version control.
