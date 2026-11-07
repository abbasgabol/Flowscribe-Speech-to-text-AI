# Optimization assessment

Date: 2 November 2026. Scope: inspection and recommendations only; no runtime,
model, installer, or website changes were made for this assessment.

## Executive recommendation

Optimize packaging first while retaining the existing model files and decoding
settings. Then offer optional installer variants if a smaller download is more
important than having both models available in one offline package.

Do not promise a particular final download size before building and measuring
candidates. Recognition quality, processing time, peak RAM, disk size, and installer
download size are separate measures; improving one does not automatically improve
the others.

## Measured baseline

The existing release installer is **672,629,666 bytes: 672.6 MB / 641.5 MiB**.
This is the downloadable setup file, not the app's RAM consumption.

The following are unpacked sizes measured from the current local build and the
specific model files selected by the installer. The current build follows the
repository reorganization; it is not an extraction of the previously published EXE.

| Component | Unpacked size | Purpose |
| --- | ---: | --- |
| `small.en` | 463.58 MiB | Larger Accuracy speech model |
| `base.en` | 140.92 MiB | Lightweight speech model |
| Punctuation model and vocabulary | 7.29 MiB | Contextual punctuation |
| Frozen app, Python, libraries, assets | 285.88 MiB | Runtime |
| Combined payload | About 897.67 MiB | Excludes separately added notices and uninstaller |

Lightweight installation selects roughly 434.09 MiB of this payload before those
extras. However, **the download still contains Accuracy**: Inno Setup component
selection happens after the complete installer has been downloaded. The Accuracy
model represents approximately 52% of the unpacked full payload.

### Largest runtime groups

These figures are parts of the 285.88 MiB runtime, not additional costs.

| Group | Size | Assessment |
| --- | ---: | --- |
| FFmpeg libraries in `av.libs` | 62.05 MiB | Large, but native dependency chain must be preserved |
| CTranslate2 | 59.36 MiB | Core speech inference; do not remove |
| Python ONNX Runtime package | 37.28 MiB | Used by Whisper's voice activity detector |
| Sherpa-ONNX | 27.71 MiB | Punctuation engine and its native dependencies |
| NumPy native libraries | 19.99 MiB | Numeric processing dependency |
| Pillow | 12.80 MiB | Tray/icon images; includes image-format plugins |
| Application EXE | 12.62 MiB | Bootloader and bundled Python modules; not just our source |
| Hugging Face Xet | 8.92 MiB | Download-related native extension; investigate exclusion |
| Tokenizers | 7.50 MiB | Recognition tokenization; retain |

Examples worth investigating: Pillow's AVIF extension alone occupies 7.53 MiB;
FFmpeg includes x265 and AV1 encoders. These are **candidates, not confirmed removable
bytes**. A DLL can be needed just to load another DLL even when the app never calls
its codec functions.

## Priority 1: preserve functionality and model quality

### A. Benchmark stronger installer compression

Current configuration: `Compression=lzma2/fast`, solid compression enabled.
Compare `normal` and `max` before considering more memory-intensive settings.

- Potential benefit: smaller download with identical extracted files.
- Recognition, model selection, installed size, and normal inference are unchanged.
- Tradeoff: build time and installation memory/time may change.
- Acceptance: identical extracted-file hashes and acceptable installation resources
  on an 8 GB PC. Savings are not yet measured; weights may compress poorly.

Inno Setup documents the compression levels and their memory tradeoffs in its
[compression reference](https://jrsoftware.org/ishelp/topic_setup_compression.htm).

### B. Replace broad package collection with reviewed hooks

`scripts/build_installer.py` currently uses `--collect-all` for Faster-Whisper,
CTranslate2, Sherpa-ONNX, and ONNX Runtime. This prioritizes successful bundling over
minimum size, pulling in submodules, data, and binaries beyond the runtime path.

Create a checked-in PyInstaller spec and small hooks that explicitly retain the
inference modules, Silero VAD asset, tokenizer resources, required DLLs, Tk, and tray
support. Review conversion tools, examples, optional format plugins, and download
backends as possible exclusions. Keep dependency versions unchanged for the first
comparison so packaging changes can be assessed independently.

- Quality should remain identical when only genuinely unused files are removed.
- Risk: missing dynamic imports or DLL dependencies may break startup or a less
  frequently used feature. A build succeeding is insufficient evidence.
- Savings: not established. The sizes above describe installed candidates, not a
  guaranteed reduction in the compressed installer.

Use PyInstaller's supported
[hooks and collection APIs](https://pyinstaller.org/en/latest/hooks.html), not manual
deletion from a finished release folder.

### C. Avoid shipping an unnecessary model for users who choose one

Offer separate offline installers, while retaining the current Complete package:

| Variant | Contains | What changes |
| --- | --- | --- |
| Complete | Both models + punctuation | Existing capabilities preserved |
| Accuracy | `small.en` + punctuation | Same Accuracy inference; base fallback unavailable until added |
| Lightweight | `base.en` + punctuation | Same Lightweight inference; Accuracy unavailable until added |

An Accuracy-only package omits 140.92 MiB of raw model files; a Lightweight-only
package omits 463.58 MiB. These are **uncompressed exclusions**, not predicted EXE
savings. Neither reduces RAM for a user already running the same selected model.

Do not silently switch an Accuracy user to `base.en` to advertise a smaller app:
that can reduce recognition accuracy. A lightweight installer is an explicit
product choice, not a no-compromise replacement for Complete.

### D. Optional model downloads, only if acceptable

A smaller core installer could download the chosen model with a clear progress
screen, resumable transfer, checksum verification, and atomic activation. Once
installed, recognition would still be offline with the same model.

This does not eliminate the model bytes or total storage. It changes initial setup
to require connectivity and introduces download failure handling. Retain a complete
offline installer for users who need offline installation. Do not describe this
as preserving every current capability unchanged.

## Priority 2: deeper optimizations requiring evidence

### Stored model quantization

The app already requests CPU `compute_type='int8'`. Runtime computation type and
the serialized model's storage representation are different concepts. Requesting
INT8 at load time does not by itself prove that the distributed weights are stored
as INT8. See [CTranslate2 quantization documentation](https://github.com/OpenNMT/CTranslate2/blob/master/docs/quantization.md).

Inspect the serialized format first. If useful, evaluate an equivalent prequantized
export of the same model. Potential disk savings could be substantial, but the
current inspection does not establish the size reduction, export equivalence, or
accuracy impact. Treat this as an experiment, not an approved zero-loss change.

### Audio decoding and native libraries

Live microphone audio already enters recognition as a NumPy array. However,
Faster-Whisper imports PyAV for file decoding, and our integration fixtures exercise
that path. Removing PyAV outright can break imports even if live capture needs no
file decoder. A smaller compatible FFmpeg build or upstream-supported lean path is
possible research work, with maintenance and binary compatibility costs.

### Two ONNX Runtime distributions

There is an ONNX DLL in the Python ONNX Runtime package and another inside
Sherpa-ONNX. They are different-sized binaries supporting different consumers.
Do not assume they are interchangeable duplicates. Sharing one requires verifying
versions, ABI, exported symbols, and provider dependencies. This is lower priority
than packaging configuration because a custom shared runtime increases maintenance.

### Duplicate tokenizer assets

The `base.en` and `small.en` tokenizer JSON and vocabulary files are byte-identical
in this checkout. Sharing them could save about 2.43 MiB of installed data, but
solid compression may already reduce download duplication. This is a small win
and introduces shared-file lifecycle concerns; defer it unless easy to support.

## RAM and speed: preserve the existing improvements

Already implemented: one speech model at a time, CPU INT8 inference, at most four
inference threads, `CT2_PACKED_GEMM=0`, lazy punctuation initialization, VAD, and a
120-second recording limit. Keep these as the baseline.

The existing `validation.json` records a base-model integration run at about
234.4 MiB resident memory and 506.6 MiB private committed memory after the pipeline.
These are historical test measurements, not a fresh idle/live microphone benchmark.
Private committed memory is not the same as physical RAM. Model selection, system
load, and recording length affect measurements.

Lower-priority runtime work: profile cold start and UI responsiveness, prevent
multiple simultaneous app instances from loading duplicate models, and consider
an opt-in idle-unload setting. Idle unloading trades lower idle RAM for slower next
dictation; it is not a free improvement. Do not change beam size, VAD behavior,
sampling rate, or punctuation settings under a requirement of unchanged behavior.

## Sustainable code and release process

1. Keep the new package structure. Separate recording, inference, and presentation
   responsibilities further only where tests and maintenance benefit; avoid a
   large rewrite just to rearrange classes.
2. Centralize release version, asset name, model manifests, and checksum metadata.
   These are currently repeated across build scripts, installer configuration, and
   website content, creating drift risk.
3. Build in a dedicated environment with pinned runtime/build dependencies. Generate
   notices for the actual bundled dependency set; currently the build iterates all
   installed distributions, including developer tooling.
4. Produce a machine-readable size inventory for each release and flag unexpected
   growth. Separate download bytes, unpacked bytes, and runtime memory in reports.
5. Automate Windows unit tests and frozen-app smoke tests; test installation and
   removal on a clean Windows VM before public releases.
6. Keep model installation transactional and preserve user preferences across
   upgrades/uninstalls. Never overwrite a published version's asset during experiments.

These changes improve maintainability and regression detection. Moving Python
files or rewriting small UI functions will not materially shrink a model-heavy
installer. A rewrite in another language is not justified by the size evidence.

## Local disk cleanup is a separate concern

The workspace contains an approximately 110 MiB incomplete model-cache file and
a 29.25 MiB punctuation download archive. The installer explicitly selects model
files and **does not include these caches**. Removing confirmed-unused leftovers
could reclaim roughly 139 MiB on the developer PC but would not shrink the EXE.
No files were deleted during this assessment.

## Validation plan and implementation order

1. Record a baseline with the exact existing models/settings. Measure cold startup,
   warm transcription latency, peak resident/committed memory, installed size,
   installer size, and install/uninstall time.
2. Test compression variants with identical payloads. Select a balanced level.
3. Trim packaging incrementally, changing one dependency group at a time.
4. Run all 31 existing tests, plus source and frozen-app smoke checks, both model
   choices, dictionary persistence, microphone capture, tray, hotkey, punctuation,
   model switching, and insertion into a controlled text editor. Include clean-PC
   installation with networking disabled.
5. Compare a consented, fixed corpus of real speech covering accents, names, times,
   lists, silence, and noisy audio. Current synthetic tests alone are insufficient
   to prove accuracy. Track word error rate and punctuation separately. Packaging-only
   changes should preserve model hashes and outputs under the same test conditions.
6. Compare repeated warm and cold timings; investigate a proposed median/p95
   regression threshold of 5%, rather than trusting one run. This threshold is a
   suggested acceptance rule, not an observed guarantee.
7. Publish measured before/after results. Evaluate installer variants or model
   re-exports only after agreeing to their specific tradeoffs.

**Recommended first implementation:** compression experiments plus a focused
PyInstaller dependency audit, retaining both original speech models and all
recognition settings. A 50–100 MB full offline installer with the same current
models is not a realistic promise without a different distribution or model-storage
strategy. Final savings remain unknown until candidate builds are measured.
