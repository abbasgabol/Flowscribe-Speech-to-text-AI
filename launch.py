"""Windowed launcher with visible startup errors."""
import ctypes
from pathlib import Path
import traceback

if __name__ == '__main__':
    try:
        from app import App
        App().root.mainloop()
    except Exception:
        log = Path(__file__).parent / 'startup.log'
        log.write_text(traceback.format_exc(), encoding='utf-8')
        ctypes.windll.user32.MessageBoxW(None,
            f'Local Dictation could not start. Run setup.bat if setup is incomplete.\n\nDetails: {log}',
            'Local Dictation', 0x10)
