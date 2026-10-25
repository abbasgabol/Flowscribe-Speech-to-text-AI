"""Conservative prose spacing, independent of neural punctuation refinement."""
import re

# Keep technical tokens and code intact. Period repair targets lower-to-upper
# sentence boundaries; ambiguous lowercase dotted identifiers are left alone.
PROTECTED = re.compile(
    r'`[^`]*`|https?://\S+|www\.\S+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}'
    r'|[A-Za-z]:[\\/][^\s]+|\b\d+(?:\.\d+)+\b'
    r'|\b(?:[A-Za-z]\.){2,}'
    r'|\b[\w-]+\.(?:com|org|net|io|dev|edu|gov|co|uk|pk|txt|py|js|json|csv|pdf|docx|xlsx)\b',
    re.I,
)

def _prose(text):
    text = re.sub(r'([?!,;:])(?=[A-Za-z])', r'\1 ', text)
    return re.sub(r'(?<=[a-z0-9])\.(?=[A-Z])', '. ', text)

def normalize_spacing(text):
    pieces, previous = [], 0
    for match in PROTECTED.finditer(text):
        pieces.extend((_prose(text[previous:match.start()]), match.group()))
        previous = match.end()
    pieces.append(_prose(text[previous:]))
    return ''.join(pieces)

def prepare_insertion(text, add_space=True):
    if add_space and text and not text[-1].isspace():
        return text + ' '
    return text
