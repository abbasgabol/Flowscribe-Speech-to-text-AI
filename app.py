"""Offline English dictation for Windows. Audio is held only in memory."""
import os
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
from win_input import HOTKEY_LABEL, Hotkey, foreground, held, insert_text
from memory_stats import snapshot
from personalization import PersonalDictionary, apply_corrections, vocabulary_hint
from punctuation import Punctuator
from speech_settings import DECODING
from text_spacing import normalize_spacing, prepare_insertion

MODEL_DIR = Path(__file__).parent / 'models' / 'base.en'
RATE = 16000

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Local Dictation')
        self.root.geometry('680x590')
        self.root.minsize(620, 530)
        self.events = queue.Queue()
        self.model = None
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
            self.dictionary = PersonalDictionary(Path(__file__).parent / 'personal_dictionary.json')
        except (ValueError, OSError) as exc:
            self.dictionary = None
            self.dictionary_error = f'Personal dictionary unavailable: {exc}'
        self.status = tk.StringVar(value='Loading local speech model...')
        self.insert = tk.BooleanVar(value=True)
        self.punctuation_enabled = tk.BooleanVar(value=True)
        self.personalization_enabled = tk.BooleanVar(value=True)
        self.add_space = tk.BooleanVar(value=True)
        self.memory_label = tk.StringVar(value='Measuring memory...')
        ttk.Label(self.root, text='Local Dictation', font=('Segoe UI', 22)).pack(pady=16)
        ttk.Label(self.root, text=f'Hold {HOTKEY_LABEL} to talk; release to finish   |   Esc: cancel').pack()
        ttk.Label(self.root, textvariable=self.status, wraplength=560).pack(pady=12)
        self.button = ttk.Button(self.root, text='Start recording', command=lambda: self.toggle(None))
        self.button.pack()
        ttk.Checkbutton(self.root, text='Insert text into the active app when using the shortcut', variable=self.insert).pack(pady=10)
        options = ttk.Frame(self.root)
        options.pack(pady=3)
        ttk.Checkbutton(options, text='Improve punctuation', variable=self.punctuation_enabled).pack(side='left', padx=8)
        ttk.Checkbutton(options, text='Use saved corrections', variable=self.personalization_enabled).pack(side='left', padx=8)
        ttk.Checkbutton(self.root, text='Add a space after inserted dictation', variable=self.add_space).pack(pady=2)
        self.output = tk.Text(self.root, height=8, wrap='word', font=('Segoe UI', 11))
        self.output.pack(fill='both', expand=True, padx=16)
        bar = ttk.Frame(self.root)
        bar.pack(pady=12)
        ttk.Button(bar, text='Copy text', command=self.copy).pack(side='left', padx=5)
        ttk.Button(bar, text='Hide to tray', command=self.root.withdraw).pack(side='left', padx=5)
        ttk.Button(bar, text='Quit', command=self.close).pack(side='left', padx=5)
        extra = ttk.Frame(self.root)
        extra.pack(pady=4)
        ttk.Button(extra, text='Personal dictionary', command=self.open_dictionary).pack(side='left', padx=5)
        ttk.Button(extra, text='View original transcript', command=self.show_original).pack(side='left', padx=5)
        ttk.Label(self.root, textvariable=self.memory_label, wraplength=640).pack(pady=8)
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
        field = tk.Text(dialog, width=75, height=12, wrap='word')
        field.pack(fill='both', expand=True, padx=12, pady=12)
        field.insert('1.0', self.last_raw or 'No transcript yet.')
        field.configure(state='disabled')

    def open_dictionary(self):
        if self.dictionary is None:
            messagebox.showerror('Personal dictionary', self.dictionary_error, parent=self.root)
            return
        dialog = tk.Toplevel(self.root)
        dialog.title('Personal dictionary — only corrections you save')
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
            if not (MODEL_DIR / 'model.bin').exists():
                raise RuntimeError('Model missing. Run setup.bat once with internet access.')
            self.model = WhisperModel(str(MODEL_DIR), device='cpu', compute_type='int8',
                                      cpu_threads=min(4, os.cpu_count() or 2), local_files_only=True)
            self.events.put(('ready', None))
        except Exception as exc:
            self.events.put(('error', str(exc)))

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
            text, notice = normalize_spacing(apply_corrections(raw, entries or {})), ''
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
                    self.status.set(self.hotkey_error or self.dictionary_error or 'Ready. Hold Win + Alt to speak. Punctuation and saved corrections run locally.')
                elif kind == 'error':
                    self.busy = self.model is None
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
