"""Format explicit clock phrases without guessing a time from a sound-alike."""
import re

HOURS = dict(zip('one two three four five six seven eight nine ten eleven twelve'.split(), range(1, 13)))
HOUR = r'(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|1[0-2]|[1-9])(?![\w-]|\.\d)'
PATTERN = re.compile(r'(?<![\w.-])(?:half\s+past|(?:a\s+)?quarter\s+(?:past|to))\s+' + HOUR, re.I)
PROTECTED = re.compile(r'`[^`]*`|https?://\S+|www\.\S+', re.I)

def _replace(match):
    parts = match.group().lower().split()
    word = parts[-1]
    hour = HOURS[word] if word in HOURS else int(word)
    if parts[0] == 'half':
        minute = 30
    elif 'to' in parts:
        hour = (hour - 2) % 12 + 1
        minute = 45
    else:
        minute = 15
    return f'{hour}:{minute:02d}'

def format_times(text):
    pieces, previous = [], 0
    for match in PROTECTED.finditer(text):
        pieces.extend((PATTERN.sub(_replace, text[previous:match.start()]), match.group()))
        previous = match.end()
    pieces.append(PATTERN.sub(_replace, text[previous:]))
    return ''.join(pieces)
