"""Windows hotkey and Unicode insertion. Does not modify the clipboard."""
import ctypes
from ctypes import wintypes as w
import threading

HOTKEY_LABEL = 'Win + Alt'

user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
user32.GetForegroundWindow.restype = w.HWND
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.PostThreadMessageW.argtypes = [w.DWORD, w.UINT, w.WPARAM, w.LPARAM]
user32.GetMessageW.argtypes = [ctypes.POINTER(w.MSG), w.HWND, w.UINT, w.UINT]
user32.RegisterHotKey.argtypes = [w.HWND, ctypes.c_int, w.UINT, w.UINT]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [('wVk', w.WORD), ('wScan', w.WORD), ('dwFlags', w.DWORD),
                ('time', w.DWORD), ('dwExtraInfo', ctypes.c_size_t)]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [('dx', w.LONG), ('dy', w.LONG), ('mouseData', w.DWORD),
                ('dwFlags', w.DWORD), ('time', w.DWORD), ('dwExtraInfo', ctypes.c_size_t)]

class INPUTUNION(ctypes.Union):
    _fields_ = [('ki', KEYBDINPUT), ('mi', MOUSEINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [('type', w.DWORD), ('data', INPUTUNION)]

user32.SendInput.argtypes = [w.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype = w.UINT

def foreground():
    return user32.GetForegroundWindow()

def held(key):
    return bool(user32.GetAsyncKeyState(key) & 0x8000)

def insert_text(text, target):
    if foreground() != target:
        return False
    encoded = text.encode('utf-16-le')
    events = []
    for i in range(0, len(encoded), 2):
        unit = int.from_bytes(encoded[i:i + 2], 'little')
        for flags in (4, 6):  # Unicode key down / up
            events.append(INPUT(1, INPUTUNION(ki=KEYBDINPUT(0, unit, flags, 0, 0))))
    if not events:
        return True
    batch = (INPUT * len(events))(*events)
    return user32.SendInput(len(events), batch, ctypes.sizeof(INPUT)) == len(events)

class HoldChord:
    """Track a modifier chord; rearm only after all Win/Alt keys are released."""
    WIN = {0x5B, 0x5C}
    ALT = {0xA4, 0xA5, 0x12}
    MODIFIERS = WIN | ALT

    def __init__(self):
        self.pressed = set()
        self.suppressed = set()
        self.active = False
        self.latched = False

    def update(self, key, down):
        suppress = key in self.suppressed
        if down:
            self.pressed.add(key)
        else:
            self.pressed.discard(key)
            self.suppressed.discard(key)
        both = bool(self.pressed & self.WIN) and bool(self.pressed & self.ALT)
        event = None
        if down and key in self.MODIFIERS and both and not self.latched and not (self.pressed - self.MODIFIERS):
            self.active = self.latched = True
            self.suppressed.add(key)
            suppress = True
            event = 'hold_start'
        elif self.active and not both:
            self.active = False
            event = 'hold_end'
        if not (self.pressed & self.MODIFIERS):
            self.latched = False
        if down and self.latched and key in self.MODIFIERS:
            suppress = True
        return event, suppress

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [('vkCode', w.DWORD), ('scanCode', w.DWORD), ('flags', w.DWORD),
                ('time', w.DWORD), ('dwExtraInfo', ctypes.c_size_t)]

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, w.WPARAM, w.LPARAM)
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, w.HINSTANCE, w.DWORD]
user32.SetWindowsHookExW.restype = w.HANDLE
user32.CallNextHookEx.argtypes = [w.HANDLE, ctypes.c_int, w.WPARAM, w.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_ssize_t
user32.UnhookWindowsHookEx.argtypes = [w.HANDLE]
kernel32.GetModuleHandleW.argtypes = [w.LPCWSTR]
kernel32.GetModuleHandleW.restype = w.HMODULE

class Hotkey:
    def __init__(self, events):
        self.events = events
        self.thread_id = None
        self.ready = threading.Event()
        self.chord = HoldChord()
        self.callback = HOOKPROC(self.on_key)
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        self.thread_id = kernel32.GetCurrentThreadId()
        # Ensure a message queue exists before close() can post WM_QUIT.
        msg = w.MSG()
        user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 0)
        hook = user32.SetWindowsHookExW(13, self.callback, kernel32.GetModuleHandleW(None), 0)
        self.ready.set()
        if not hook:
            self.events.put(('hotkey_error', f'{HOTKEY_LABEL} is unavailable (Windows error {ctypes.get_last_error()}). Use the recording button.'))
            return
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                pass
        finally:
            user32.UnhookWindowsHookEx(hook)

    def on_key(self, code, message, address):
        if code >= 0 and message in (0x100, 0x101, 0x104, 0x105):
            data = ctypes.cast(address, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            if not data.flags & 0x10:  # Ignore synthesized input, including our own typing.
                event, suppress = self.chord.update(data.vkCode, message in (0x100, 0x104))
                if event == 'hold_start':
                    target = foreground()
                    # Mask standalone Win/Alt menu activation for the first, forwarded key.
                    mask = (INPUT * 2)(
                        INPUT(1, INPUTUNION(ki=KEYBDINPUT(0xE8, 0, 0, 0, 0))),
                        INPUT(1, INPUTUNION(ki=KEYBDINPUT(0xE8, 0, 2, 0, 0))))
                    user32.SendInput(2, mask, ctypes.sizeof(INPUT))
                    self.events.put((event, target))
                elif event:
                    self.events.put((event, None))
                if suppress:
                    return 1
        return user32.CallNextHookEx(None, code, message, address)

    def close(self):
        if self.ready.wait(1) and self.thread_id:
            user32.PostThreadMessageW(self.thread_id, 0x0012, 0, 0)
            self.thread.join(timeout=1)
