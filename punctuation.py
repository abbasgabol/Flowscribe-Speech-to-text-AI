"""Small local punctuation model, preserving words and existing sentence endings."""
from pathlib import Path
import re
from text_spacing import normalize_spacing
from app_paths import MODEL_ROOT

MODEL_DIR = MODEL_ROOT / 'punctuation'
WORDS = re.compile(r"\w+(?:['’\-]\w+)*", re.UNICODE)

class Punctuator:
    def __init__(self):
        self.engine = None

    def load(self):
        if self.engine is None:
            import sherpa_onnx as sherpa
            if not (MODEL_DIR / 'model.int8.onnx').is_file():
                raise RuntimeError('Punctuation model missing. Run setup.bat to download it.')
            self.engine = sherpa.OnlinePunctuation(sherpa.OnlinePunctuationConfig(
                sherpa.OnlinePunctuationModelConfig(
                    cnn_bilstm=str(MODEL_DIR / 'model.int8.onnx'),
                    bpe_vocab=str(MODEL_DIR / 'bpe.vocab'), num_threads=1, provider='cpu')))

    def restore(self, text):
        text = normalize_spacing(text)
        if not text.strip():
            return text
        # Preserve technical strings, quoted text, numeric punctuation and line structure.
        if re.search(r'://|[@_/\\`"<>]|\d[.,:]\d', text):
            return text
        self.load()
        lines = []
        for line in text.split('\n'):
            sentences = re.split(r'(?<=[.!?])\s+', line.strip())
            lines.append(' '.join(self.sentence(s) for s in sentences))
        return '\n'.join(lines)

    def sentence(self, text):
        words = WORDS.findall(text)
        if not words or len(words) > 120:
            return text
        existing_end = re.search(r'[.!?]+$', text)
        # Short, already-punctuated sentences usually benefit more from preservation.
        if existing_end and len(words) <= 12:
            return text
        # Never pass existing punctuation to the model: it would duplicate marks.
        result = self.engine.add_punctuation_with_case(' '.join(words).lower())
        predicted = WORDS.findall(result)
        if [w.casefold() for w in words] != [w.casefold() for w in predicted]:
            return text
        index = iter(enumerate(words))
        def preserve_names(match):
            i, original = next(index)
            # Preserve original internal capitalization and capitalized names.
            return original if (i > 0 and original != original.lower()) or any(c.isupper() for c in original[1:]) else match.group()
        result = WORDS.sub(preserve_names, result).strip()
        if existing_end:
            result = re.sub(r'[.!?,;:]+$', '', result) + existing_end.group()
        elif result and result[-1] not in '.!?':
            result = result.rstrip(',;:') + '.'
        return result
