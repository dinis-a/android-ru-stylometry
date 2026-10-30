"""What the app says about a text: the model's answer, how far to trust it, and why.

Nothing here imports Flet, so the rules can be tested without a window. The model itself is in
ru_detector and is left as the notebook wrote it.
"""

import math
import re
from dataclasses import dataclass, field

import samples

# The model works well on paragraphs and badly on a few words: on the texts of tests/corpus.py cut
# to their first words it was right for 94% of them at 16 words and for all of them from 30,
# while below 8 words it called almost every machine text "human". The app still answers for a
# shorter text, but says that the answer is poor.
SHORT_WORDS = 30

CHUNK_CHARS = 900  # about 200 tokens of Russian; the model reads 256 at most
MAX_CHUNKS = 6  # a longer text is read in part, to keep the wait on a phone short
UNSURE = 0.25  # an answer this close to the model's threshold is "cannot tell"
MIN_GAP = 3.0  # self-check: machine text must score this far above human text (log-odds)

_WORD = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*")
_SENTENCE_END = re.compile(r"[.!?…]+[»”)]*(?=\s)|\n")


@dataclass
class Verdict:
    kind: str  # "ai", "human", "unsure" or "foreign"
    p_ai: float | None  # the model's probability of the machine class; None if it was not asked
    words: int
    chars: int = 0
    pieces: int = 0  # how many pieces of the text the model read
    unread: int = 0  # characters at the end of the text that were left out
    notes: list = field(default_factory=list)  # "short", "unformatted", "partial"


def count_words(text):
    """Words in the text: runs of letters, with a hyphenated word counted once."""
    return len(_WORD.findall(text))


def logit(p):
    """Log-odds of a probability, finite even for 0 and 1."""
    p = min(max(p, 1e-12), 1 - 1e-12)
    return math.log(p) - math.log1p(-p)


def cyrillic_share(text):
    """Share of Cyrillic letters among all the letters of the text."""
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return 0.0
    return sum("Ѐ" <= ch <= "ӿ" for ch in letters) / len(letters)


def unformatted(text):
    """No capital letters or no sentence marks: the model takes such text for a human's."""
    return not any(ch.isupper() for ch in text) or not re.search(r"[.!?…]", text)


def _cut(text, start, size):
    """Where to end the piece that begins at `start`: after a sentence, else at a space."""
    window = text[start : start + size]
    ends = [m.end() for m in _SENTENCE_END.finditer(window)]
    if ends and ends[-1] >= size // 2:
        return ends[-1]
    space = window.rfind(" ")
    return space if space >= size // 2 else size


def split_text(text, size=CHUNK_CHARS, limit=MAX_CHUNKS):
    """The first `limit` pieces of about `size` characters, and how many characters are left.

    The pieces are the text itself (newlines included), cut after a sentence where possible.
    """
    pieces, start, end = [], 0, len(text)
    while start < end and len(pieces) < limit:
        if end - start <= size * 5 // 4:  # the last piece may run over rather than leave a stub
            stop = end
        else:
            stop = start + _cut(text, start, size)
        piece = text[start:stop].strip()
        if piece:
            pieces.append(piece)
        start = stop
        while start < end and text[start].isspace():
            start += 1
    return pieces, end - start


def decide(p_ai, threshold):
    """Return "ai", "human" or "unsure" for a probability of the machine class."""
    if p_ai >= threshold + UNSURE:
        return "ai"
    if p_ai <= threshold - UNSURE:
        return "human"
    return "unsure"


def assess(detector, text):
    """The verdict on a text; raises ValueError if there is nothing to check."""
    text = text.strip() if isinstance(text, str) else ""
    if not text:
        raise ValueError("the text is empty")
    words = count_words(text)
    if cyrillic_share(text) < 0.5:  # the model has seen Russian only: its answer would be noise
        return Verdict("foreign", None, words, chars=len(text))
    pieces, unread = split_text(text)
    answers = [detector.predict(piece) for piece in pieces]
    if len(answers) == 1:
        p_ai = answers[0]["p_ai"]  # the answer of the model as it is
    else:
        # a piece with more tokens is more evidence: average the log-odds with that weight
        tokens = sum(a["tokens"] for a in answers)
        margin = sum(logit(a["p_ai"]) * a["tokens"] for a in answers) / tokens
        p_ai = 1 / (1 + math.exp(-margin))

    verdict = Verdict(
        decide(p_ai, detector.threshold),
        p_ai,
        words,
        chars=len(text),
        pieces=len(pieces),
        unread=unread,
    )
    if words < SHORT_WORDS:
        verdict.notes.append("short")
    if unformatted(text):
        verdict.notes.append("unformatted")
    if unread:
        verdict.notes.append("partial")
    return verdict


def health_check(detector):
    """Why the model would answer everything alike, or None if it tells two texts apart.

    The app runs this on start: on a phone the build of onnxruntime or tokenizers may differ
    from the one the model was checked with, and nothing else would show it.
    """
    try:
        human = logit(detector.predict(samples.HUMAN)["p_ai"])
        machine = logit(detector.predict(samples.MACHINE)["p_ai"])
    except Exception as error:  # a broken file or library
        return f"{type(error).__name__}: {error}"
    if machine - human < MIN_GAP:
        return (
            f"the chatbot sample scores {machine:+.1f} and the Gogol sample {human:+.1f}, "
            f"less than {MIN_GAP:g} apart"
        )
    return None
