import os
os.environ['CT2_PACKED_GEMM'] = '0'
os.environ['HF_HUB_OFFLINE'] = '1'
import json
from pathlib import Path
import time
from faster_whisper import WhisperModel
from punctuation import Punctuator

model = WhisperModel('models/base.en', device='cpu', compute_type='int8', cpu_threads=4, local_files_only=True)
punctuator = Punctuator()
report = []
for filename in ('sample.wav', 'sample-context.wav'):
    for label, options in (
        ('original_beam3', {'beam_size': 3}),
        ('beam5', {'beam_size': 5}),
        ('beam5_punctuation_example', {'beam_size': 5,
            'initial_prompt': "Hello. How are you? I'm doing well, thank you."}),
    ):
        start = time.perf_counter()
        segments, _ = model.transcribe(str(Path('tests') / filename), language='en',
            vad_filter=True, condition_on_previous_text=False, **options)
        raw = ' '.join(s.text.strip() for s in segments)
        report.append({'sample': filename, 'configuration': label, 'raw': raw,
            'seconds': round(time.perf_counter() - start, 3), 'refined': punctuator.restore(raw)})
Path('decoding-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
