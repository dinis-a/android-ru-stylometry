"""Tests for the rules that turn the model's answers into a verdict. Run with `python run_tests.py`."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import samples  # noqa: E402
import verdict as v  # noqa: E402

PARAGRAPH = (
    "Это первое предложение достаточно длинного текста, которое написано аккуратно. "
    "Второе предложение продолжает мысль и добавляет подробностей для читателя. "
    "Третье предложение завершает абзац и подводит небольшой итог всему сказанному."
)


class Fake:
    """A detector that answers `p_ai` (a number, or a function of the text) and keeps its calls."""

    threshold = 0.5

    def __init__(self, p_ai):
        self.p_ai = p_ai
        self.calls = []

    def predict(self, text):
        self.calls.append(text)
        p = self.p_ai(text) if callable(self.p_ai) else self.p_ai
        return {"label": "ai", "p_ai": p, "tokens": max(1, len(text) // 4), "truncated": False}


def test_nothing_to_check_is_an_error():
    for blank in ("", "   \n ", None, 5):
        try:
            v.assess(Fake(0.9), blank)
        except ValueError:
            continue
        raise AssertionError(f"{blank!r} was accepted")


def test_the_verdict_follows_the_probability():
    for p, kind in ((0.99, "ai"), (0.75, "ai"), (0.7499, "unsure"), (0.5, "unsure"), (0.2501, "unsure"), (0.25, "human"), (0.01, "human")):
        assert v.assess(Fake(p), PARAGRAPH * 2).kind == kind, p


def test_a_short_text_is_checked_all_the_same():
    detector = Fake(0.99)
    result = v.assess(detector, "Привет, как дела?")
    assert result.kind == "ai" and result.p_ai > 0.9  # the answer of the model is not withheld
    assert "short" in result.notes and detector.calls
    assert v.assess(Fake(0.99), "Привет").kind == "ai"


def test_a_text_of_a_paragraph_is_not_called_short():
    text = " ".join(["слово"] * v.SHORT_WORDS).capitalize() + "."
    assert "short" not in v.assess(Fake(0.9), text).notes
    assert "short" in v.assess(Fake(0.9), " ".join(["слово"] * (v.SHORT_WORDS - 1)).capitalize() + ".").notes


def test_text_that_is_not_russian_is_not_sent_to_the_model():
    detector = Fake(0.99)
    for text in ("The quick brown fox jumps over the lazy dog.", "1234567890 1234567890", "!!! ???"):
        result = v.assess(detector, text)
        assert result.kind == "foreign" and result.p_ai is None, text
    assert detector.calls == []


def test_text_without_capitals_or_stops_is_flagged_but_the_answer_stays():
    lower = PARAGRAPH.lower()
    result = v.assess(Fake(0.01), lower)
    assert result.kind == "human" and "unformatted" in result.notes
    assert "unformatted" in v.assess(Fake(0.99), PARAGRAPH.replace(".", "")).notes
    assert "unformatted" not in v.assess(Fake(0.99), PARAGRAPH).notes


def test_a_long_text_is_read_in_pieces_and_the_log_odds_are_averaged():
    text = " ".join([PARAGRAPH] * 12)  # about 3000 characters: several pieces
    answers = iter([0.99, 0.5, 0.2, 0.9, 0.6, 0.7, 0.3])
    detector = Fake(lambda piece: next(answers))
    result = v.assess(detector, text)
    assert result.pieces == len(detector.calls) > 1 and result.unread == 0
    weights = [max(1, len(piece) // 4) for piece in detector.calls]
    expected = sum(w * v.logit(p) for w, p in zip(weights, [0.99, 0.5, 0.2, 0.9, 0.6, 0.7, 0.3])) / sum(weights)
    assert abs(result.p_ai - 1 / (1 + math.exp(-expected))) < 1e-9


def test_the_text_beyond_the_last_piece_is_reported():
    text = (PARAGRAPH + " ") * 60
    detector = Fake(0.9)
    result = v.assess(detector, text)
    assert len(detector.calls) == v.MAX_CHUNKS == result.pieces
    assert result.unread > 0 and "partial" in result.notes
    assert result.chars - result.unread <= v.MAX_CHUNKS * v.CHUNK_CHARS * 5 // 4 + 1


def test_a_huge_text_is_cut_without_copying_the_rest_over_and_over():
    pieces, unread = v.split_text("слово " * 1_000_000)
    assert len(pieces) == v.MAX_CHUNKS and unread > 5_000_000


def test_pieces_are_the_text_itself_cut_after_sentences():
    text = (PARAGRAPH + "\n") * 40
    pieces, unread = v.split_text(text, size=500, limit=100)
    assert unread == 0 and len(pieces) > 5
    assert all(piece and piece == piece.strip() for piece in pieces)
    assert all(len(piece) <= 500 * 5 // 4 for piece in pieces)
    assert "".join(pieces).replace(" ", "").replace("\n", "") == text.replace(" ", "").replace("\n", "")
    assert all(piece.endswith(".") for piece in pieces[:-1])  # cut where a sentence ends
    assert any("\n" in piece for piece in pieces)  # the line breaks stay in the text


def test_a_text_without_spaces_is_cut_hard():
    pieces, unread = v.split_text("а" * 3000, size=900, limit=10)
    # the rest is cut while it is longer than a piece and a quarter; a shorter one is the last piece
    assert [len(p) for p in pieces] == [900, 900, 900, 300] and unread == 0


def test_words_are_runs_of_letters():
    assert v.count_words("Мама мыла раму.") == 3
    assert v.count_words("по-своему — NN, 1984 год") == 3  # a hyphenated word is one; dashes and numbers are not
    assert v.count_words("") == 0


def test_share_of_cyrillic_letters():
    assert v.cyrillic_share("Привет") == 1.0
    assert v.cyrillic_share("hello") == 0.0
    assert v.cyrillic_share("123 !?") == 0.0
    assert abs(v.cyrillic_share("Приве hello") - 0.5) < 1e-9


def test_log_odds_stay_finite_at_the_extremes():
    assert math.isfinite(v.logit(0.0)) and math.isfinite(v.logit(1.0))
    assert v.logit(0.5) == 0 and v.logit(0.9) > 0 > v.logit(0.1)


def test_the_self_check_passes_for_a_model_that_tells_the_samples_apart():
    detector = Fake(lambda text: 0.99 if text == samples.MACHINE else 0.01)
    assert v.health_check(detector) is None


def test_the_self_check_catches_a_model_that_answers_everything_alike():
    problem = v.health_check(Fake(0.7))
    assert problem and "less than" in problem


def test_the_self_check_catches_a_model_that_has_the_samples_the_wrong_way_round():
    assert v.health_check(Fake(lambda text: 0.01 if text == samples.MACHINE else 0.99))


def test_the_self_check_reports_a_model_that_fails():
    class Broken(Fake):
        def predict(self, text):
            raise OSError("model.onnx is missing")

    assert "OSError: model.onnx is missing" == v.health_check(Broken(0.5))
