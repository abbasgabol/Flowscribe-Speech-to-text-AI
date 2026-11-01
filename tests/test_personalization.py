import tempfile
from pathlib import Path
import unittest
from local_dictation.personalization import PersonalDictionary, apply_corrections, vocabulary_hint

class DictionaryTests(unittest.TestCase):
    def test_only_explicit_saves_create_files_and_persist(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / 'dictionary.json'
            store = PersonalDictionary(path)
            self.assertFalse(path.exists())
            store.add('open eye', 'OpenAI')
            self.assertEqual(PersonalDictionary(path).entries, {'open eye': 'OpenAI'})
            store.remove('open eye')
            self.assertEqual(PersonalDictionary(path).entries, {})

    def test_boundaries_case_and_non_cascading(self):
        self.assertEqual(apply_corrections('Art and cart. OPEN EYE.', {'art': 'craft', 'craft': 'work', 'open eye': 'OpenAI'}),
                         'craft and cart. OpenAI.')

    def test_longest_phrase_wins(self):
        self.assertEqual(apply_corrections('new york city', {'new york': 'NY', 'new york city': 'NYC'}), 'NYC')

    def test_hint_is_bounded(self):
        self.assertLessEqual(len(vocabulary_hint({str(i): 'word' * 30 + str(i) for i in range(200)})), 500)

    def test_invalid_and_oversized_corrections(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            store = PersonalDictionary(Path(directory) / 'dictionary.json')
            for source, target in [('', 'name'), ('hello', ''), ('x' * 121, 'name'), ('hello\nworld', 'name')]:
                with self.assertRaises(ValueError):
                    store.add(source, target)
