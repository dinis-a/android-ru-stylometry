"""Tests for the neural model that gives the main answer. Run with `python run_tests.py`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import samples  # noqa: E402
import verdict as v  # noqa: E402
from ru_detector import Detector  # noqa: E402
from tests.corpus import HUMAN, MACHINE  # noqa: E402

DETECTOR = Detector()


def margins(group):
    return [v.logit(DETECTOR.predict(text)["p_ai"]) for text in group.values()]


def test_the_answer_is_not_the_same_for_every_text():
    scores = margins(HUMAN) + margins(MACHINE)
    assert len({round(score, 2) for score in scores}) >= 15, "a model that answers one thing to everything"
    assert max(scores) - min(scores) > 15


def test_machine_texts_score_above_human_ones():
    human, machine = margins(HUMAN), margins(MACHINE)
    pairs = [(m > h) + 0.5 * (m == h) for m in machine for h in human]
    assert sum(pairs) / len(pairs) >= 0.85  # separation of the two groups (AUC)
    correct = sum(m >= 0 for m in machine) + sum(h < 0 for h in human)
    assert correct / (len(human) + len(machine)) >= 0.8


def test_the_samples_of_the_app_are_judged_as_labelled():
    assert v.assess(DETECTOR, samples.MACHINE).kind == "ai"
    assert v.assess(DETECTOR, samples.HUMAN).kind == "human"


def test_the_self_check_of_the_app_passes_for_the_shipped_model():
    assert v.health_check(DETECTOR) is None


def test_the_same_text_gives_the_same_answer():
    assert DETECTOR.predict(samples.MACHINE) == DETECTOR.predict(samples.MACHINE)


def test_empty_texts_are_refused():
    for blank in ("", "  ", None):
        try:
            DETECTOR.predict(blank)
        except ValueError:
            continue
        raise AssertionError(f"{blank!r} was accepted")


def test_a_long_text_is_reported_as_cut():
    assert DETECTOR.predict("слово " * 2000)["truncated"] is True
    assert DETECTOR.predict(samples.MACHINE)["truncated"] is False


def test_a_long_text_is_read_in_pieces():
    machine = v.assess(DETECTOR, " ".join(MACHINE.values()))
    assert machine.pieces >= 2 and machine.kind == "ai"
    human = v.assess(DETECTOR, " ".join(HUMAN.values()))
    assert human.pieces >= 2 and human.p_ai < 0.5
