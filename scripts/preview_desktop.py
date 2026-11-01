"""Capture the actual interface with explicitly illustrative transcript content."""
import _bootstrap  # Allow direct execution from any working directory.
import time
from pathlib import Path
from PIL import ImageGrab
from PIL import Image
import ctypes
from ctypes import wintypes
from local_dictation.app import App

app = App(model_name='base.en', persist_settings=False)
try:
    end = time.monotonic() + 90
    while app.loading and time.monotonic() < end:
        app.root.update()
        time.sleep(.05)
    assert app.model is not None, app.status.get()
    app.root.geometry('880x720+60+60')
    app.root.deiconify()
    app.root.lift()
    app.root.attributes('-topmost', True)
    app.output.insert('1.0', 'Our train was scheduled to arrive at 8:30, but it was an hour late.\n\nLet’s make a little more room for the next idea.')
    app.status.set('Example transcript · Hold Win + Alt in a text field to try your own.')
    for _ in range(20):
        app.root.update()
        time.sleep(.05)
    x, y = app.root.winfo_rootx(), app.root.winfo_rooty()
    image = ImageGrab.grab(bbox=(x, y, x + app.root.winfo_width(), y + app.root.winfo_height()))
    if True:
        # PrintWindow also renders when the desktop capture surface is unavailable.
        user32, gdi = ctypes.windll.user32, ctypes.windll.gdi32
        user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        user32.GetAncestor.restype = wintypes.HWND
        user32.GetDC.argtypes = [wintypes.HWND]
        user32.GetDC.restype = wintypes.HDC
        gdi.CreateCompatibleDC.argtypes = [wintypes.HDC]
        gdi.CreateCompatibleDC.restype = wintypes.HDC
        gdi.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
        gdi.CreateCompatibleBitmap.restype = wintypes.HBITMAP
        gdi.SelectObject.argtypes = [wintypes.HDC, wintypes.HANDLE]
        gdi.SelectObject.restype = wintypes.HANDLE
        user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
        gdi.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT, ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT]
        gdi.DeleteObject.argtypes = [wintypes.HANDLE]
        gdi.DeleteDC.argtypes = [wintypes.HDC]
        user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
        handle = user32.GetAncestor(app.root.winfo_id(), 2)
        width, height = app.root.winfo_width(), app.root.winfo_height()
        dc = user32.GetDC(handle)
        memory = gdi.CreateCompatibleDC(dc)
        bitmap = gdi.CreateCompatibleBitmap(dc, width, height)
        old = gdi.SelectObject(memory, bitmap)
        try:
            assert user32.PrintWindow(handle, memory, 1), 'PrintWindow failed'
            import struct
            header = ctypes.create_string_buffer(struct.pack('<IiiHHIIiiII', 40, width, -height, 1, 32, 0, width*height*4, 0, 0, 0, 0))
            pixels = ctypes.create_string_buffer(width*height*4)
            gdi.SelectObject(memory, old)
            assert gdi.GetDIBits(memory, bitmap, 0, height, pixels, header, 0)
            image = Image.frombuffer('RGB', (width,height), pixels, 'raw', 'BGRX', 0, 1)
        finally:
            gdi.DeleteObject(bitmap)
            gdi.DeleteDC(memory)
            user32.ReleaseDC(handle, dc)
    assert image.convert('RGB').getbbox() is not None, 'Desktop screenshot is blank'
    image.save(Path(__file__).resolve().parents[1] / 'website' / 'dist' / 'desktop-preview.png')
    print('Desktop preview captured; local model loaded successfully.')
finally:
    app.close()
