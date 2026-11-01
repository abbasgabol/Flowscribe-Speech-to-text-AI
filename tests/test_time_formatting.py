import unittest
from local_dictation.time_formatting import format_times

class ClockTests(unittest.TestCase):
    def test_requested_phrase(self):
        self.assertEqual(format_times('Our train was scheduled to arrive at half past eight, but it was an hour late.'),
                         'Our train was scheduled to arrive at 8:30, but it was an hour late.')

    def test_quarters_and_wraparound(self):
        self.assertEqual(format_times('Quarter past six; a quarter to nine; quarter to one; half past 12.'),
                         '6:15; 8:45; 12:45; 12:30.')

    def test_no_guessed_corrections(self):
        for text in ('The half car seat is broken.', 'Half past thirteen.', 'half past eighty',
                     'half past 123', 'half past 8.5', 'half past eight-year-olds', '8:30', 'half an hour',
                     '`half past eight`', 'https://example.com/half-past-eight'):
            self.assertEqual(format_times(text), text)

    def test_no_am_pm_assumptions(self):
        self.assertEqual(format_times('Half past eight in the evening'), '8:30 in the evening')
