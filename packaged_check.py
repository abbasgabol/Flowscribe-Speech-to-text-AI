"""Non-recording smoke test used by the release build to verify the frozen app."""
import json
import time
from app_paths import APP_DIR, DATA_DIR

def run(report_path, audio_path):
    from app import App
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
        report_path.write_text(json.dumps({'gui': 'passed', 'hotkey': 'passed', 'transcript': app.last_raw,
            'punctuation': punctuation, 'app_dir': str(APP_DIR), 'data_dir': str(DATA_DIR)}, indent=2), encoding='utf-8')
    finally:
        app.close()
