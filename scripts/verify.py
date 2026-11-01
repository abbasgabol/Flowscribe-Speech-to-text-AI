"""Integration check; no microphone recording or typing into other applications."""
import _bootstrap  # Allow direct execution from any working directory.
import json
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import time
import sys

os.environ['HF_HUB_OFFLINE'] = '1'
import numpy as np
import sounddevice as sd
from local_dictation.app import App
from local_dictation.win_input import foreground, insert_text, user32
from local_dictation.speech_settings import DECODING
from local_dictation.memory_stats import snapshot

if __name__ == '__main__':
    app = App(model_name=sys.argv[1] if len(sys.argv) > 1 else None, persist_settings=False)
    app.root.withdraw()
    report = {}
    try:
        deadline = time.monotonic() + 90
        while app.busy and time.monotonic() < deadline:
            app.root.update()
            if app.status.get().startswith('Error:'):
                raise RuntimeError(app.status.get())
            time.sleep(.05)
        assert app.model is not None and not app.busy, 'Model did not become ready'
        assert not app.hotkey_error, app.hotkey_error
        report['gui_and_hotkey'] = 'passed'
        report['speech_model'] = app.current_model
        app.refresh_memory()
        assert 'App RAM:' in app.memory_label.get()
        app.open_dictionary()
        app.show_original()
        app.root.update()
        for child in app.root.winfo_children():
            if child.winfo_class() == 'Toplevel':
                child.destroy()
        report['memory_and_personalization_ui'] = 'passed'
        app.root.deiconify()
        app.output.focus_force()
        app.root.update()
        user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        user32.GetAncestor.restype = wintypes.HWND
        target = user32.GetAncestor(app.root.winfo_id(), 2)
        if app.root.focus_get() == app.output and foreground() == target:
            assert insert_text('Insertion test.', target), 'Windows rejected insertion'
            for _ in range(10):
                app.root.update()
                time.sleep(.02)
            assert app.output.get('1.0', 'end-1c') == 'Insertion test.', repr(app.output.get('1.0', 'end-1c'))
            report['unicode_insertion_in_test_editor'] = 'passed'
            app.output.delete('1.0', 'end')
            app.deliver('Last night?', target, time.monotonic() + 3)
            for _ in range(10):
                app.root.update()
                time.sleep(.02)
            app.deliver('As she replied.', target, time.monotonic() + 3)
            for _ in range(10):
                app.root.update()
                time.sleep(.02)
            assert app.output.get('1.0', 'end-1c') == 'Last night? As she replied. '
            report['sequential_dictation_spacing'] = 'passed'
        else:
            report['unicode_insertion_in_test_editor'] = 'skipped: test editor did not get focus'
        app.root.withdraw()
        report['input_devices'] = [d['name'] for d in sd.query_devices() if d['max_input_channels'] > 0]
        start = time.monotonic()
        segments, _ = app.model.transcribe(np.zeros(16000 * 3, dtype=np.float32), language='en', vad_filter=True)
        assert not ''.join(s.text for s in segments).strip(), 'Silence produced text'
        report['silence'] = 'passed'
        sample = Path(__file__).resolve().parents[1] / 'tests' / 'sample.wav'
        if sample.exists():
            start = time.monotonic()
            segments, info = app.model.transcribe(str(sample), **DECODING)
            text = ' '.join(s.text.strip() for s in segments)
            report['sample_transcript'] = text
            report['sample_audio_seconds'] = round(info.duration, 2)
            report['sample_processing_seconds'] = round(time.monotonic() - start, 2)
            assert 'offline dictation' in text.lower(), text
            assert '?' in text and '.' in text, 'Expected sentence and question punctuation'
            app.transcribe(str(sample), None, False, True, {})
            app.root.update()
            deadline = time.monotonic() + 5
            while not app.last_raw and time.monotonic() < deadline:
                app.root.update()
                time.sleep(.05)
            assert app.last_raw, 'Full transcription pipeline did not publish original text'
            assert app.output.get('1.0', 'end-1c'), 'Full pipeline produced no preview'
            report['full_pipeline'] = 'passed'
        example = "hey john i was wondering if you could send me that file actually never mind i'll do it myself thanks"
        refined = app.punctuator.restore(example)
        assert 'Hey, John,' in refined and "I'll do it myself." in refined, refined
        report['context_punctuation'] = refined
        time_sample = Path('tests/sample-time.wav')
        if time_sample.exists():
            app.last_raw = ''
            app.transcribe(str(time_sample), None, False, True, {})
            deadline = time.monotonic() + 5
            while not app.last_raw and time.monotonic() < deadline:
                app.root.update()
                time.sleep(.05)
            final = app.output.get('1.0', 'end-1c')
            assert '8:30' in final, final
            report['clock_phrase_pipeline'] = final
        report['memory_after_pipeline'] = snapshot()
        if (Path('models/small.en/model.bin')).exists():
            original_model = app.current_model
            alternate = 'base.en' if original_model == 'small.en' else 'small.en'
            for name in (alternate, original_model):
                app.model_choice.set('Accuracy — small.en' if name == 'small.en' else 'Lightweight — base.en')
                app.switch_model()
                deadline = time.monotonic() + 90
                while app.busy and time.monotonic() < deadline:
                    app.root.update()
                    if app.status.get().startswith('Error:'):
                        raise RuntimeError(app.status.get())
                    time.sleep(.05)
                assert app.current_model == name and app.model is not None and not app.busy
            report['model_switch_roundtrip'] = 'passed'
        print(json.dumps(report, indent=2), flush=True)
        Path('validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    finally:
        app.close()
