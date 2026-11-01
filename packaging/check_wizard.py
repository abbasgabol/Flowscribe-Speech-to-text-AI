"""Inspect the setup wizard without installing; capture only its own window."""
import ctypes as c
from ctypes import wintypes as w
import json
from pathlib import Path
import struct
import subprocess
import time
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
u, g = c.windll.user32, c.windll.gdi32
u.SetProcessDPIAware()
CALLBACK = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
u.FindWindowW.argtypes = [w.LPCWSTR, w.LPCWSTR]; u.FindWindowW.restype = w.HWND
u.EnumChildWindows.argtypes = [w.HWND, CALLBACK, w.LPARAM]
u.GetWindowTextW.argtypes = [w.HWND, w.LPWSTR, c.c_int]
u.IsWindowVisible.argtypes = [w.HWND]
u.IsWindowEnabled.argtypes = [w.HWND]
u.SendMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
u.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
u.GetWindowRect.argtypes = [w.HWND, c.POINTER(w.RECT)]
u.GetDC.argtypes = [w.HWND]; u.GetDC.restype = w.HDC
u.PrintWindow.argtypes = [w.HWND, w.HDC, w.UINT]
u.ReleaseDC.argtypes = [w.HWND, w.HDC]
g.CreateCompatibleDC.argtypes = [w.HDC]; g.CreateCompatibleDC.restype = w.HDC
g.CreateCompatibleBitmap.argtypes = [w.HDC,c.c_int,c.c_int]; g.CreateCompatibleBitmap.restype = w.HBITMAP
g.SelectObject.argtypes = [w.HDC,w.HANDLE]; g.SelectObject.restype = w.HANDLE
g.GetDIBits.argtypes = [w.HDC,w.HBITMAP,w.UINT,w.UINT,c.c_void_p,c.c_void_p,w.UINT]
g.DeleteObject.argtypes = [w.HANDLE]; g.DeleteDC.argtypes = [w.HDC]

def controls(window):
    result = []
    @CALLBACK
    def visit(hwnd, _):
        if u.IsWindowVisible(hwnd):
            text = c.create_unicode_buffer(2048)
            u.GetWindowTextW(hwnd, text, len(text))
            if text.value:
                result.append({'handle':hwnd, 'text':text.value, 'enabled':bool(u.IsWindowEnabled(hwnd))})
        return True
    u.EnumChildWindows(window, visit, 0)
    return result

def click(window, phrase):
    item = next(i for i in controls(window) if i['text'].replace('&','').startswith(phrase))
    assert item['enabled'], item
    u.PostMessageW(item['handle'], 0xF5, 0, 0)
    time.sleep(.35)

def capture(window, name):
    rect = w.RECT(); u.GetWindowRect(window,c.byref(rect))
    width,height=rect.right-rect.left,rect.bottom-rect.top
    dc=u.GetDC(window); memory=g.CreateCompatibleDC(dc)
    bitmap=g.CreateCompatibleBitmap(dc,width,height); old=g.SelectObject(memory,bitmap)
    try:
        assert u.PrintWindow(window,memory,2)
        g.SelectObject(memory,old)
        pixels=c.create_string_buffer(width*height*4)
        header=c.create_string_buffer(struct.pack('<IiiHHIIiiII',40,width,-height,1,32,0,width*height*4,0,0,0,0))
        assert g.GetDIBits(memory,bitmap,0,height,pixels,header,0)
        Image.frombuffer('RGB',(width,height),pixels,'raw','BGRX',0,1).save(ROOT/'qa'/name)
    finally:
        g.DeleteObject(bitmap); g.DeleteDC(memory); u.ReleaseDC(window,dc)

process=subprocess.Popen([str(ROOT/'website/dist/downloads/LocalDictation-Setup.exe'), '/LANG=english'], creationflags=subprocess.CREATE_NO_WINDOW)
window=None
try:
    deadline=time.monotonic()+30
    while not window and time.monotonic()<deadline:
        time.sleep(.2); window=u.FindWindowW(None,'Setup - Local Dictation')
    assert window, 'Setup window did not appear'
    time.sleep(.5)
    capture(window,'installer-welcome.png')
    click(window,'Next')
    license_controls=controls(window)
    assert any('accept' in i['text'] for i in license_controls)
    assert not next(i for i in license_controls if 'Next' in i['text'])['enabled']
    capture(window,'installer-license.png')
    click(window,'I accept')
    click(window,'Next')
    click(window,'Next')
    folder_controls=controls(window)
    assert any('Browse' in i['text'] for i in folder_controls), folder_controls
    capture(window,'installer-location.png')
    click(window,'Next')
    assert any('Accuracy' in i['text'] or 'Components' in i['text'] for i in controls(window))
    click(window,'Next')
    assert any('shortcut' in i['text'].lower() or 'Tasks' in i['text'] for i in controls(window))
    print(json.dumps({'welcome':'passed','license_required':'passed','destination_picker':'passed','components':'passed','shortcuts':'passed'}))
finally:
    if window:
        # Close the inspected wizard before the actual isolated installation test.
        u.PostMessageW(window,0x10,0,0)
        time.sleep(.4)
        dialog=u.FindWindowW(None,'Exit Setup')
        if dialog: click(dialog,'Yes')
