"""Windowed launcher with visible startup errors."""
import ctypes
from pathlib import Path
import traceback
import sys
from app_paths import data_file

if __name__ == '__main__':
    try:
        if '--self-test' in sys.argv:
            from packaged_check import run
            run(Path(sys.argv[sys.argv.index('--self-test') + 1]), sys.argv[-1])
        else:
            from app import App
            App().root.mainloop()
    except Exception:
        log = data_file('startup.log')
        log.write_text(traceback.format_exc(), encoding='utf-8')
        if '--self-test' in sys.argv:
            Path(sys.argv[sys.argv.index('--self-test') + 1]).write_text(traceback.format_exc(), encoding='utf-8')
            sys.exit(1)
        ctypes.windll.user32.MessageBoxW(None,
            f'Local Dictation could not start. Repair the installation if setup is incomplete.\n\nDetails: {log}',
            'Local Dictation', 0x10)
