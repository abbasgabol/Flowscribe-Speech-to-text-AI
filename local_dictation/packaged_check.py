"""Non-recording smoke test used by the release build to verify the frozen app."""
import json
import time
import io
import sys
from local_dictation.app_paths import APP_DIR, DATA_DIR

def run(report_path, audio_path):
    from local_dictation.app import App, MODEL_CHOICES
    app = App(model_name='base.en', persist_settings=False)
    app.root.withdraw()
    try:
        deadline = time.monotonic() + 90
        while app.loading and time.monotonic() < deadline:
            app.root.update()
            time.sleep(.05)
        assert app.model is not None and not app.hotkey_error, app.status.get()
        app.transcribe(audio_path, None, False, True, {})
        app.root.update()
        assert 'offline dictation' in app.output.get('1.0', 'end').lower(), app.status.get()
        app.open_dictionary()
        app.show_original()
        app.root.update()
        punctuation = app.punctuator.restore('hello there how are you doing today i hope everything is going well')
        assert app.punctuator.engine is not None
        report = {'gui': 'passed', 'hotkey': 'passed', 'transcript': app.last_raw,
            'punctuation': punctuation, 'app_dir': str(APP_DIR), 'data_dir': str(DATA_DIR)}
        if '--all-models' in sys.argv:
            # Exercise dynamic imports/assets that packaging exclusions could break.
            from pathlib import Path
            import numpy as np
            from faster_whisper.audio import decode_audio
            from PIL import Image
            from local_dictation.speech_settings import DECODING
            for icon in (app.idle_icon, app.recording_icon):
                stream = io.BytesIO()
                icon.save(stream, format='ICO')
                stream.seek(0)
                Image.open(stream).load()
            report['tray_icon_roundtrip'] = 'passed'
            report['models'] = {}
            for model_name in ('base.en', 'small.en'):
                if model_name != app.current_model:
                    app.model_choice.set(next(k for k, v in MODEL_CHOICES.items() if v == model_name))
                    app.switch_model()
                    deadline = time.monotonic() + 90
                    while app.loading and time.monotonic() < deadline:
                        app.root.update()
                        time.sleep(.05)
                    assert app.current_model == model_name and app.model is not None and not app.busy, app.status.get()
                samples = {}
                for name in ('sample.wav', 'sample-context.wav', 'sample-time.wav'):
                    audio = Path(audio_path).with_name(name)
                    assert audio.is_file(), str(audio)
                    wave = decode_audio(str(audio))
                    trials, outputs = [], []
                    for _ in range(3):
                        started = time.perf_counter()
                        segments, _ = app.model.transcribe(wave, **DECODING)
                        outputs.append(' '.join(s.text.strip() for s in segments))
                        trials.append(round(time.perf_counter() - started, 4))
                    assert outputs[0] == outputs[1] == outputs[2]
                    samples[name] = {'transcript':outputs[0], 'seconds':trials}
                segments, _ = app.model.transcribe(np.zeros(48000, dtype=np.float32), **DECODING)
                assert not ''.join(s.text for s in segments).strip()
                report['models'][model_name] = {'samples':samples, 'silence':'passed'}
        report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    finally:
        app.close()
