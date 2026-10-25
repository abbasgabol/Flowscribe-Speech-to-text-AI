"""Measure actual memory and punctuation overhead using generated test audio."""
import json
import os
from pathlib import Path
import time
import sys
from memory_stats import snapshot

os.environ['HF_HUB_OFFLINE'] = '1'
report = {'start': snapshot()}
from faster_whisper import WhisperModel
report['speech_imported'] = snapshot()
model = WhisperModel('models/base.en', device='cpu', compute_type='int8', cpu_threads=4, local_files_only=True)
report['speech_loaded'] = snapshot()
sample = Path('tests/sample.wav')
if sample.exists():
    start = time.perf_counter()
    segments, _ = model.transcribe(str(sample), language='en', beam_size=3, vad_filter=True,
                                   condition_on_previous_text=False)
    report['transcript'] = ' '.join(s.text.strip() for s in segments)
    report['speech_seconds'] = round(time.perf_counter() - start, 3)
report['after_transcription'] = snapshot()
from punctuation import Punctuator
punctuator = Punctuator()
punctuator.load()
report['punctuation_loaded'] = snapshot()
samples = ['how are you i am fine thank you',
           'i went to the market bought apples oranges and milk then i came home',
           'Hello, this is a test of offline dictation. Can you hear me clearly?',
           'I use VS Code and OpenAI every day.', 'my email is test@example.com']
report['punctuation_examples'] = []
for text in samples:
    start = time.perf_counter()
    result = punctuator.restore(text)
    report['punctuation_examples'].append({'input': text, 'output': result,
        'milliseconds': round((time.perf_counter() - start) * 1000, 2)})
report['after_punctuation'] = snapshot()
Path(sys.argv[1] if len(sys.argv) > 1 else 'memory-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2), flush=True)
