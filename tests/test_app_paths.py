import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

def load_paths():
    spec = importlib.util.spec_from_file_location('isolated_app_paths', ROOT/'app_paths.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class PathTests(unittest.TestCase):
    def test_source_paths_preserved(self):
        module = load_paths()
        self.assertEqual(module.MODEL_ROOT, ROOT/'models')
        self.assertEqual(module.DATA_DIR, ROOT)

    def test_installed_data_separate_from_resources(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tests') as temp:
            with patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'executable', str(ROOT/'dist/Test/App.exe')), patch.object(sys, '_MEIPASS', str(ROOT/'dist/Test/_internal'), create=True), patch.dict(os.environ, {'LOCALAPPDATA':temp}):
                module = load_paths()
                self.assertEqual(module.MODEL_ROOT, ROOT/'dist/Test/models')
                self.assertEqual(module.RESOURCE_DIR, ROOT/'dist/Test/_internal')
                self.assertEqual(module.data_file('settings.json'), Path(temp)/'LocalDictation/settings.json')
                self.assertTrue(module.DATA_DIR.is_dir())

if __name__ == '__main__':
    unittest.main()
