import unittest
from unittest.mock import Mock
from win_input import HoldChord
from app import App


class HoldTests(unittest.TestCase):
    def test_either_press_and_release_order(self):
        for first, second in ((0x5B, 0xA4), (0xA4, 0x5B), (0x5C, 0xA5)):
            for released in (first, second):
                chord = HoldChord()
                self.assertEqual(chord.update(first, True), (None, False))
                self.assertEqual(chord.update(second, True), ('hold_start', True))
                self.assertEqual(chord.update(second, True), (None, True))
                self.assertEqual(chord.update(released, False)[0], 'hold_end')
                remaining = second if released == first else first
                self.assertIsNone(chord.update(remaining, False)[0])
                self.assertFalse(chord.latched)

    def test_forwarded_key_up_is_not_swallowed(self):
        chord = HoldChord()
        chord.update(0x5B, True)
        chord.update(0xA4, True)
        self.assertEqual(chord.update(0x5B, False), ('hold_end', False))
        self.assertEqual(chord.update(0xA4, False), (None, True))

    def test_rearm_requires_full_release(self):
        chord = HoldChord()
        chord.update(0x5B, True)
        chord.update(0xA4, True)
        chord.update(0xA4, False)
        self.assertIsNone(chord.update(0xA4, True)[0])
        chord.update(0xA4, False)
        chord.update(0x5B, False)
        chord.update(0x5B, True)
        self.assertEqual(chord.update(0xA4, True)[0], 'hold_start')

    def test_other_shortcut_does_not_activate(self):
        chord = HoldChord()
        for key in (0xA2, 0x5B, 0xA4):
            self.assertIsNone(chord.update(key, True)[0])
        self.assertIsNone(chord.update(0xA2, False)[0])

    def test_app_starts_and_stops_only_hold_recordings(self):
        app = Mock(busy=False, stream=None, hold_recording=False)
        App.handle_hold(app, 'hold_start', 123)
        app.start_recording.assert_called_once_with(123, from_hold=True)
        app.stream = object()
        App.handle_hold(app, 'hold_end')
        app.stop.assert_not_called()
        app.hold_recording = True
        App.handle_hold(app, 'hold_end')
        app.stop.assert_called_once()

    def test_busy_app_ignores_hold(self):
        app = Mock(busy=True, stream=None, hold_recording=False)
        App.handle_hold(app, 'hold_start', 123)
        App.handle_hold(app, 'hold_end')
        app.start_recording.assert_not_called()
        app.stop.assert_not_called()


if __name__ == '__main__':
    unittest.main()
