import unittest
from local_dictation.text_spacing import normalize_spacing, prepare_insertion

class SpacingTests(unittest.TestCase):
    def test_reported_boundaries(self):
        self.assertEqual(normalize_spacing('last night?As she replied. Pick her up?I thought. Pick her up.So it ended.'),
                         'last night? As she replied. Pick her up? I thought. Pick her up. So it ended.')

    def test_common_punctuation(self):
        self.assertEqual(normalize_spacing('Yes,no!Wait;please:listen'), 'Yes, no! Wait; please: listen')

    def test_existing_whitespace_is_preserved(self):
        text = 'Done.\nNext paragraph?  Yes.\n\nEnd.'
        self.assertEqual(normalize_spacing(text), text)

    def test_technical_tokens_are_preserved(self):
        text = '3.14 v1.2.3 U.S.A. test@example.com example.COM https://site.io/a?b=c `a.b?c:d` C:\\Files\\App.py'
        self.assertEqual(normalize_spacing(text), text)

    def test_sequential_insertions_are_separated(self):
        self.assertEqual(prepare_insertion('Last night?') + prepare_insertion('As she replied.'),
                         'Last night? As she replied. ')

    def test_insertion_option_and_existing_space(self):
        for text in ('', 'already ', 'paragraph\n'):
            self.assertEqual(prepare_insertion(text), text)
        self.assertEqual(prepare_insertion('Done.', False), 'Done.')
