"""Cached morphological analysis on top of pymorphy3."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, NamedTuple, Optional

# The dictionaries are shipped with the app (stylometry/dicts) and not read from the package
# pymorphy3-dicts-ru: on Android all packages are packed into one zip file, and pymorphy3 opens
# its dictionaries as ordinary files, which fails inside a zip.
DICTIONARIES = Path(__file__).resolve().parent.parent / "dicts"

_analyzer: Any = None


class WordInfo(NamedTuple):
    """The grammatical facts about one word that the morphological features need."""

    pos: Optional[str]
    case: Optional[str]
    tense: Optional[str]
    person: Optional[str]
    lemma: str
    is_known: bool


def get_analyzer() -> Any:
    """Return a shared ``pymorphy3.MorphAnalyzer``; dictionaries are loaded on first use."""
    global _analyzer
    if _analyzer is None:
        import pymorphy3

        _analyzer = pymorphy3.MorphAnalyzer(path=str(DICTIONARIES), lang="ru")
    return _analyzer


@lru_cache(maxsize=100_000)
def analyze_word(word: str) -> WordInfo:
    """Analyse a lowercase word and keep its most probable parse.

    Results are cached per process: word frequencies follow Zipf's law, so a few thousand
    entries cover most of the running text and pymorphy3 parses each of them only once.
    """
    parse = get_analyzer().parse(word)[0]
    tag = parse.tag
    return WordInfo(tag.POS, tag.case, tag.tense, tag.person, parse.normal_form, parse.is_known)
