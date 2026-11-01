"""Separate installed resources from writable, per-user preferences."""
import os
import sys
from pathlib import Path

FROZEN = getattr(sys, 'frozen', False)
APP_DIR = Path(sys.executable).parent if FROZEN else Path(__file__).parent
RESOURCE_DIR = Path(getattr(sys, '_MEIPASS', APP_DIR))
DATA_DIR = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'LocalDictation' if FROZEN else APP_DIR
MODEL_ROOT = APP_DIR / 'models'

def data_file(name):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / name
