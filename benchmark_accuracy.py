"""Compare speech models on identical generated fixtures in separate processes."""
import os
os.environ['CT2_PACKED_GEMM'] = '0'
os.environ['HF_HUB_OFFLINE'] = '1'
import json
from pathlib import Path
import sys
import time
from faster_whisper import WhisperModel
from speech_settings import DECODING
from time_formatting import format_times
from memory_stats import snapshot

name = sys.argv[1] if len(sys.argv) > 1 else 'base.en'
start = time.perf_counter()
model = WhisperModel(str(Path('models') / name), device='cpu', compute_type='int8',
                     cpu_threads=4, local_files_only=True)
report = {'model': name, 'load_seconds': round(time.perf_counter() - start, 2),
          'memory_loaded': snapshot(), 'samples': []}
for filename in ('sample-time.wav', 'sample.wav', 'sample-context.wav'):
    source = Path('tests') / filename
    if not source.exists():
        continue
    start = time.perf_counter()
    segments, info = model.transcribe(str(source), **DECODING)
    raw = ' '.join(s.text.strip() for s in segments)
    report['samples'].append({'file': filename, 'audio_seconds': round(info.duration, 2),
        'processing_seconds': round(time.perf_counter() - start, 2),
        'raw': raw, 'formatted': format_times(raw)})
report['memory_after'] = snapshot()
Path(f'accuracy-report-{name}.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2), flush=True)
