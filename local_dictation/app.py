"""Offline English dictation for Windows. Audio is held only in memory."""
import os
import gc
import json
# Reduce CPU memory prepacking overhead; measured on the target i5 laptop.
os.environ.setdefault('CT2_PACKED_GEMM', '0')
from pathlib import Path
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import numpy as np
import pyperclip
import pystray
import sounddevice as sd
from PIL import Image, ImageDraw
from faster_whisper import WhisperModel
from local_dictation.win_input import HOTKEY_LABEL, Hotkey, foreground, held, insert_text
from local_dictation.memory_stats import snapshot
from local_dictation.personalization import PersonalDictionary, apply_corrections, vocabulary_hint
from local_dictation.punctuation import Punctuator
from local_dictation.speech_settings import DECODING
from local_dictation.text_spacing import normalize_spacing, prepare_insertion
from local_dictation.time_formatting import format_times
from local_dictation.app_paths import MODEL_ROOT, RESOURCE_DIR, data_file, FROZEN

MODEL_DIR = MODEL_ROOT / 'base.en'
MODEL_CHOICES = {'Lightweight — base.en': 'base.en', 'Accuracy — small.en': 'small.en'}
SETTINGS_PATH = data_file('app_settings.json')
RATE = 16000

class App:
    def __init__(self, model_name=None, persist_settings=True):
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
        self.root = tk.Tk()
        self.root.tk.call('tk', 'scaling', 96 / 72)
        self.root.title('Local Dictation')
        icon_path = RESOURCE_DIR / 'app.ico'
        if icon_path.is_file():
            self.root.iconbitmap(str(icon_path))
        self.root.geometry('680x640')
        self.root.minsize(620, 600)
        self.events = queue.Queue()
        self.model = None
        default_model = 'small.en' if (MODEL_DIR.parent / 'small.en' / 'model.bin').exists() else 'base.en'
        try:
            saved_model = json.loads(SETTINGS_PATH.read_text(encoding='utf-8')).get('model', default_model)
        except (OSError, ValueError, AttributeError):
            saved_model = default_model
        self.current_model = model_name or (saved_model if saved_model in MODEL_CHOICES.values() else default_model)
        self.loading = True
        self.persist_settings = persist_settings
        self.stream = None
        self.hold_recording = False
        self.frames = []
        self.busy = True
        self.target = None
        self.closed = False
        self.hotkey_error = ''
        self.last_raw = ''
        self.punctuator = Punctuator()
        self.dictionary_error = ''
        try:
            self.dictionary = PersonalDictionary(data_file('personal_dictionary.json'))
        except (ValueError, OSError) as exc:
            self.dictionary = None
            self.dictionary_error = f'Personal dictionary unavailable: {exc}'
        self.status = tk.StringVar(value='Loading local speech model...')
        self.insert = tk.BooleanVar(value=True)
        self.punctuation_enabled = tk.BooleanVar(value=True)
        self.personalization_enabled = tk.BooleanVar(value=True)
        self.add_space = tk.BooleanVar(value=True)
        self.memory_label = tk.StringVar(value='Measuring memory...')
        from local_dictation.desktop_ui import build
        build(self, MODEL_CHOICES)
        self.root.protocol('WM_DELETE_WINDOW', self.root.withdraw)
        self.hotkey = Hotkey(self.events)
        icon = Image.new('RGB', (64, 64), '#173c42')
        draw = ImageDraw.Draw(icon)
        draw.rounded_rectangle((25, 10, 39, 39), radius=7, fill='#a5f3dc')
        draw.arc((18, 22, 46, 48), 0, 180, fill='white', width=4)
        draw.line((32, 48, 32, 56), fill='white', width=4)
        self.idle_icon = icon
        self.recording_icon = icon.copy()
        ImageDraw.Draw(self.recording_icon).ellipse((42, 2, 62, 22), fill='#ff4545')
        self.tray = pystray.Icon('local-dictation', icon, 'Local Dictation', menu=pystray.Menu(
            pystray.MenuItem('Open', lambda *_: self.events.put(('show', None)), default=True),
            pystray.MenuItem('Quit', lambda *_: self.events.put(('quit', None)))))
        threading.Thread(target=self.tray.run, daemon=True).start()
        threading.Thread(target=self.load, daemon=True).start()
        self.root.after(50, self.poll)
        self.root.after(1000, self.refresh_memory)

    def refresh_memory(self):
        if self.closed:
            return
        try:
            values = snapshot()
            self.memory_label.set(f"App RAM: {values['ram_mb']:.0f} MB | Private committed: {values['private_commit_mb']:.0f} MB\n"
                                  f"PC available RAM: {values['system_available_mb']:.0f} MB")
        except OSError:
            self.memory_label.set('Memory counters unavailable.')
        self.root.after(3000, self.refresh_memory)

    def show_original(self):
        dialog = tk.Toplevel(self.root)
        dialog.title('Original recognition — before punctuation and saved corrections')
        dialog.configure(bg='#f5f4ef')
        field = tk.Text(dialog, width=75, height=12, wrap='word', font=('Segoe UI', 12),
                        relief='flat', padx=18, pady=18, bg='white', fg='#203c35')
        field.pack(fill='both', expand=True, padx=12, pady=12)
        field.insert('1.0', self.last_raw or 'No transcript yet.')
        field.configure(state='disabled')

    def open_dictionary(self):
        if self.dictionary is None:
            messagebox.showerror('Personal dictionary', self.dictionary_error, parent=self.root)
            return
        dialog = tk.Toplevel(self.root)
        dialog.title('Personal dictionary — only corrections you save')
        dialog.configure(bg='#f5f4ef')
        dialog.geometry('660x450')
        ttk.Label(dialog, text='Save a recurring misheard word or phrase. It will be replaced wherever it occurs.\n'
                  'Your preferred spelling is also a vocabulary hint. No conversations are saved.', wraplength=630).pack(pady=10)
        table = ttk.Treeview(dialog, columns=('heard', 'preferred'), show='headings', height=9)
        table.heading('heard', text='Heard phrase')
        table.heading('preferred', text='Use instead')
        table.pack(fill='both', expand=True, padx=12)
        form = ttk.Frame(dialog)
        form.pack(fill='x', padx=12, pady=10)
        heard, preferred = tk.StringVar(), tk.StringVar()
        ttk.Label(form, text='Heard phrase').grid(row=0, column=0, sticky='w')
        ttk.Entry(form, textvariable=heard, width=34).grid(row=1, column=0, padx=4)
        ttk.Label(form, text='Use instead').grid(row=0, column=1, sticky='w')
        ttk.Entry(form, textvariable=preferred, width=34).grid(row=1, column=1, padx=4)
        def refresh():
            for item in table.get_children():
                table.delete(item)
            for source, target in self.dictionary.entries.items():
                table.insert('', 'end', values=(source, target))
        def select(_):
            if table.selection():
                source, target = table.item(table.selection()[0], 'values')
                heard.set(source)
                preferred.set(target)
        def save():
            try:
                self.dictionary.add(heard.get(), preferred.get())
                refresh()
                self.status.set('Correction saved locally. It will apply to future dictation.')
            except (ValueError, OSError) as exc:
                messagebox.showerror('Could not save correction', str(exc), parent=dialog)
        def remove():
            if table.selection():
                try:
                    self.dictionary.remove(table.item(table.selection()[0], 'values')[0])
                    refresh()
                except OSError as exc:
                    messagebox.showerror('Could not delete correction', str(exc), parent=dialog)
        table.bind('<<TreeviewSelect>>', select)
        actions = ttk.Frame(dialog)
        actions.pack(pady=8)
        ttk.Button(actions, text='Save correction', command=save).pack(side='left', padx=5)
        ttk.Button(actions, text='Delete selected', command=remove).pack(side='left', padx=5)
        ttk.Button(actions, text='Close', command=dialog.destroy).pack(side='left', padx=5)
        refresh()

    def load(self):
        try:
            folder = MODEL_DIR.parent / self.current_model
            if not (folder / 'model.bin').exists():
                raise RuntimeError('Model missing. Run the installer again to repair the installation.' if FROZEN else 'Model missing. Run scripts/setup.bat or scripts/setup_accuracy.bat with internet access.')
            # Release the old model before allocating the new one.
            self.model = None
            gc.collect()
            self.model = WhisperModel(str(folder), device='cpu', compute_type='int8',
                                      cpu_threads=min(4, os.cpu_count() or 2), local_files_only=True)
            self.events.put(('ready', None))
        except Exception as exc:
            self.events.put(('error', str(exc)))

    def switch_model(self, _=None):
        selected = MODEL_CHOICES[self.model_choice.get()]
        if self.loading or self.stream is not None or (self.busy and self.model is not None):
            self.model_choice.set(next(label for label, name in MODEL_CHOICES.items() if name == self.current_model))
            self.status.set('Finish the current recording or transcription before changing models.')
            return
        if not (MODEL_DIR.parent / selected / 'model.bin').exists():
            self.model_choice.set(next(label for label, name in MODEL_CHOICES.items() if name == self.current_model))
            self.status.set('Run the installer again and select the Accuracy model.' if FROZEN else 'Accuracy model is not installed. Run scripts/setup_accuracy.bat once.')
            return
        if selected == self.current_model and self.model is not None:
            return
        self.current_model = selected
        self.loading = self.busy = True
        self.model_selector.configure(state='disabled')
        self.status.set(f'Loading {selected} locally...')
        threading.Thread(target=self.load, daemon=True).start()

    def toggle(self, target):
        if self.busy:
            return
        if self.stream is not None:
            self.stop()
            return
        self.start_recording(target)

    def handle_hold(self, event, target=None):
        if event == 'hold_start':
            if not self.busy and self.stream is None:
                self.start_recording(target, from_hold=True)
        elif self.hold_recording and self.stream is not None:
            self.stop()

    def start_recording(self, target, from_hold=False):
        # A button click always transcribes into the preview only.
        self.target = target if self.insert.get() else None
        self.frames = []
        self.overflow = False
        self.hold_recording = from_hold
        try:
            self.stream = sd.InputStream(samplerate=RATE, channels=1, dtype='float32', callback=self.audio)
            self.stream.start()
            self.started = time.monotonic()
            self.status.set('Listening... Release Win or Alt to finish.' if from_hold else 'Listening... Click Stop and transcribe to finish.')
            self.tray.title = 'Local Dictation — Recording'
            self.tray.icon = self.recording_icon
            self.button.configure(text='Stop and transcribe')
        except Exception as exc:
            if self.stream:
                self.stream.close()
            self.stream = None
            self.hold_recording = False
            self.status.set(f'Microphone error: {exc}')

    def audio(self, data, frames, timing, status):
        self.frames.append(data[:, 0].copy())
        if status:
            self.overflow = True

    def stop(self):
        self.hold_recording = False
        self.stream.stop()
        self.stream.close()
        self.stream = None
        self.button.configure(text='Start recording')
        self.tray.title = 'Local Dictation — Processing'
        self.tray.icon = self.idle_icon
        if not self.frames:
            self.status.set('No audio recorded.')
            return
        samples = np.concatenate(self.frames)
        self.frames = []
        self.busy = True
        self.status.set('Transcribing locally...')
        entries = dict(self.dictionary.entries) if self.dictionary and self.personalization_enabled.get() else {}
        threading.Thread(target=self.transcribe,
                         args=(samples, self.target, self.overflow, self.punctuation_enabled.get(), entries), daemon=True).start()

    def transcribe(self, samples, target, overflow, improve_punctuation=True, entries=None):
        try:
            started = time.monotonic()
            segments, _ = self.model.transcribe(samples, **DECODING,
                                                hotwords=vocabulary_hint(entries or {}) or None)
            raw = ' '.join(s.text.strip() for s in segments).strip()
            text, notice = normalize_spacing(format_times(apply_corrections(raw, entries or {}))), ''
            if improve_punctuation and text:
                try:
                    text = self.punctuator.restore(text)
                except Exception as exc:
                    notice = f'Punctuation unavailable; kept original recognition. {exc}'
            text = normalize_spacing(text)
            self.events.put(('result', (text, target, time.monotonic() - started, overflow, raw, notice)))
        except Exception as exc:
            self.events.put(('error', str(exc)))

    def cancel(self):
        self.hold_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            self.frames = []
            self.status.set('Recording cancelled.')
            self.tray.title = 'Local Dictation'
            self.tray.icon = self.idle_icon
            self.button.configure(text='Start recording')

    def copy(self):
        try:
            pyperclip.copy(self.output.get('1.0', 'end-1c'))
            self.status.set('Copied to clipboard.')
        except Exception as exc:
            self.status.set(f'Could not copy: {exc}')

    def poll(self):
        if self.stream:
            if held(0x1B):
                self.cancel()
            elif time.monotonic() - self.started >= 120:
                self.stop()
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind in ('hold_start', 'hold_end'):
                    self.handle_hold(kind, value)
                elif kind == 'show':
                    self.root.deiconify()
                    self.root.lift()
                elif kind == 'quit':
                    self.close()
                    return
                elif kind == 'hotkey_error':
                    self.hotkey_error = value
                    self.status.set(value)
                elif kind == 'ready':
                    self.busy = False
                    self.loading = False
                    self.model_selector.configure(state='readonly')
                    try:
                        if self.persist_settings:
                            temporary = SETTINGS_PATH.with_suffix('.tmp')
                            temporary.write_text(json.dumps({'model': self.current_model}), encoding='utf-8')
                            temporary.replace(SETTINGS_PATH)
                    except OSError:
                        pass  # A read-only installation can still dictate.
                    self.status.set(self.hotkey_error or self.dictionary_error or 'Ready. Hold Win + Alt to speak. Punctuation and saved corrections run locally.')
                elif kind == 'error':
                    self.busy = self.model is None
                    self.loading = False
                    self.model_selector.configure(state='readonly')
                    self.status.set(f'Error: {value}')
                    self.root.deiconify()
                    self.tray.title = 'Local Dictation — Error'
                elif kind == 'result':
                    text, target, elapsed, overflow, self.last_raw, notice = value
                    self.output.delete('1.0', 'end')
                    self.output.insert('1.0', text)
                    self.tray.title = 'Local Dictation'
                    self.status.set(f'Done in {elapsed:.1f}s.' if text else 'No speech detected.')
                    if notice:
                        self.status.set(notice)
                    if overflow:
                        self.status.set('Microphone dropped audio. Review the transcript below.')
                    if text and target and not overflow:
                        self.deliver(text, target, time.monotonic() + 3)
                    else:
                        self.busy = False
        except queue.Empty:
            pass
        if not self.closed:
            self.root.after(50, self.poll)

    def deliver(self, text, target, deadline):
        if self.closed:
            return
        if foreground() != target:
            self.busy = False
            self.status.set('Active window changed. Use Copy text to insert manually.')
            return
        if any(held(k) for k in (0x10, 0x11, 0x12, 0x5B, 0x5C, 0x20)):
            if time.monotonic() < deadline:
                self.root.after(100, lambda: self.deliver(text, target, deadline))
                return
            self.status.set('Shortcut keys still held. Use Copy text to insert manually.')
        elif not insert_text(prepare_insertion(text, self.add_space.get()), target):
            self.status.set('This app blocked insertion. Use Copy text to insert manually.')
        self.busy = False

    def close(self):
        self.closed = True
        self.cancel()
        self.hotkey.close()
        self.tray.stop()
        self.root.destroy()

if __name__ == '__main__':
    App().root.mainloop()
