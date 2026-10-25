"""Bounded, explicit phrase corrections. No passive transcript collection or training."""
import json
from pathlib import Path
import re

MAX_ENTRIES = 200
MAX_PHRASE = 120

def apply_corrections(text, entries):
    if not entries:
        return text
    replacements = {source.casefold(): target for source, target in entries.items()}
    pattern = re.compile(r'(?<!\w)(?:' + '|'.join(re.escape(s) for s in sorted(entries, key=len, reverse=True)) + r')(?!\w)', re.I)
    return pattern.sub(lambda match: replacements[match.group().casefold()], text)

def vocabulary_hint(entries):
    # Bound decoding context; later entries represent more recently saved preferences.
    terms = list(dict.fromkeys(entries.values()))[-30:]
    result = []
    for term in reversed(terms):
        if sum(len(t) + 2 for t in result) + len(term) > 500:
            break
        result.append(term)
    return ', '.join(result)

class PersonalDictionary:
    def __init__(self, path):
        self.path = Path(path)
        self.entries = {}
        if self.path.exists():
            if self.path.stat().st_size > 250000:
                raise ValueError('Personal dictionary file exceeds the size limit.')
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or len(data) > MAX_ENTRIES:
                raise ValueError('Invalid personal dictionary.')
            for source, target in data.items():
                self.validate(source, target)
            self.entries = data

    @staticmethod
    def validate(source, target):
        if not isinstance(source, str) or not isinstance(target, str):
            raise ValueError('Corrections must be text.')
        if not source.strip() or not target.strip() or max(len(source), len(target)) > MAX_PHRASE:
            raise ValueError('Enter a phrase and correction, each at most 120 characters.')
        if '\n' in source + target:
            raise ValueError('Use single-line words or phrases.')

    def save(self, entries):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(self.path)
        self.entries = entries

    def add(self, source, target):
        source, target = source.strip(), target.strip()
        self.validate(source, target)
        updated = {s: t for s, t in self.entries.items() if s.casefold() != source.casefold()}
        if len(updated) >= MAX_ENTRIES:
            raise ValueError('The dictionary is full (200 entries). Delete an old correction first.')
        updated[source] = target
        self.save(updated)

    def remove(self, source):
        self.save({s: t for s, t in self.entries.items() if s != source})
