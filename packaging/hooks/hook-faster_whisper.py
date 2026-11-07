"""Keep packaged VAD assets while normal analysis follows inference imports."""
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('faster_whisper', includes=['assets/*'])
