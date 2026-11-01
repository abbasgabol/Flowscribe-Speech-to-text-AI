import ctypes
import unittest
from unittest.mock import patch

from local_dictation import win_input


class InsertionTests(unittest.TestCase):
    def test_changed_window_does_not_type(self):
        with patch.object(win_input, 'foreground', return_value=22), patch.object(win_input.user32, 'SendInput') as send:
            self.assertFalse(win_input.insert_text('private text', 11))
            send.assert_not_called()

    def test_unicode_pairs_and_surrogates(self):
        captured = []
        def send(count, inputs, size):
            self.assertEqual(size, 40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28)
            captured.extend((inputs[i].data.ki.wScan, inputs[i].data.ki.dwFlags) for i in range(count))
            return count
        with patch.object(win_input, 'foreground', return_value=11), patch.object(win_input.user32, 'SendInput', side_effect=send):
            self.assertTrue(win_input.insert_text('A\U0001f600', 11))
        self.assertEqual(captured, [(65, 4), (65, 6), (0xD83D, 4), (0xD83D, 6), (0xDE00, 4), (0xDE00, 6)])

    def test_blocked_insertion_is_reported(self):
        with patch.object(win_input, 'foreground', return_value=11), patch.object(win_input.user32, 'SendInput', return_value=0):
            self.assertFalse(win_input.insert_text('hello', 11))


if __name__ == '__main__':
    unittest.main()
