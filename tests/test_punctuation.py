import unittest
from unittest.mock import Mock
from local_dictation.punctuation import Punctuator

class PunctuationTests(unittest.TestCase):
    def setUp(self):
        self.p = Punctuator()
        self.p.engine = Mock()

    def test_existing_short_question_is_preserved(self):
        text = 'Can you hear me clearly?'
        self.assertEqual(self.p.restore(text), text)
        self.p.engine.add_punctuation_with_case.assert_not_called()

    def test_technical_strings_are_preserved(self):
        for text in ['email test@example.com', 'visit https://example.com', 'cost 3.14', 'file_name', 'Arrive at 8:30.']:
            self.assertEqual(self.p.restore(text), text)
        self.p.engine.add_punctuation_with_case.assert_not_called()

    def test_rejects_word_changes(self):
        self.p.engine.add_punctuation_with_case.return_value = 'I can go.'
        self.assertEqual(self.p.restore('i cannot go'), 'i cannot go')

    def test_adds_punctuation_without_changing_names(self):
        self.p.engine.add_punctuation_with_case.return_value = 'I use openai, every day'
        self.assertEqual(self.p.restore('i use OpenAI every day'), 'I use OpenAI, every day.')

    def test_silence_never_loads_model(self):
        self.assertEqual(self.p.restore(''), '')
        self.p.engine.add_punctuation_with_case.assert_not_called()
