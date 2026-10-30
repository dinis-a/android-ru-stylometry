"""Tests for the stylometric second opinion. Run with `python run_tests.py` (needs pymorphy3).

tests/fixtures/stylometry_reference.json holds what ru-stylometry and scikit-learn give for 25
texts; tools/export_stylometry.py writes it. The app has to give the same.
"""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from stylometry import StyleAnalyzer  # noqa: E402
from stylometry.boost import Boosting  # noqa: E402
from stylometry.lib import DEFAULT_GROUPS, describe_features  # noqa: E402

FIXTURES = json.loads((ROOT / "tests" / "fixtures" / "stylometry_reference.json").read_text(encoding="utf-8"))
ANALYZER = StyleAnalyzer()
EXACT = 1e-9


def test_the_reference_covers_texts_of_every_kind():
    ids = {case["id"] for case in FIXTURES}
    assert len(FIXTURES) >= 25 and "one-word" in ids and "long-machine" in ids
    assert {i.split("-")[0] for i in ids} >= {"human", "machine", "sample"}


def test_the_features_are_those_of_ru_stylometry():
    for case in FIXTURES:
        expected = [case["features"][name] for name in ANALYZER.columns]
        assert np.allclose(ANALYZER.features(case["text"]), expected, rtol=0, atol=EXACT), case["id"]


def test_the_probabilities_are_those_of_scikit_learn():
    for case in FIXTURES:
        assert abs(ANALYZER.analyze(case["text"]).p_ai - case["p_ai"]) < EXACT, case["id"]


def test_the_reasons_are_those_of_ru_stylometry():
    for case in FIXTURES:
        report = ANALYZER.analyze(case["text"])
        effects = {reason.feature: reason.effect for reason in report.reasons}
        for name, expected in zip(ANALYZER.columns, case["feature_effects"]):
            assert abs(effects[name] - expected) < EXACT, (case["id"], name)
        assert set(report.groups) == set(case["group_effects"])
        for group, expected in case["group_effects"].items():
            assert abs(report.groups[group] - expected) < EXACT, (case["id"], group)


def test_the_strongest_reasons_come_first():
    report = ANALYZER.analyze(FIXTURES[0]["text"])
    sizes = [abs(reason.effect) for reason in report.reasons]
    assert sizes == sorted(sizes, reverse=True) and len(sizes) == len(ANALYZER.columns)
    group_sizes = [abs(effect) for effect in report.groups.values()]
    assert group_sizes == sorted(group_sizes, reverse=True)


def test_a_reason_says_what_its_effect_is_measured_against():
    reason = ANALYZER.analyze(FIXTURES[0]["text"]).reasons[0]
    index = ANALYZER.columns.index(reason.feature)
    assert reason.typical == ANALYZER.baseline[index] and reason.group == ANALYZER.group_of[index]


def test_a_text_with_typical_features_has_no_reasons():
    class Typical(StyleAnalyzer):
        def features(self, text):
            return self.baseline.copy()

    report = Typical().analyze("любой текст")
    assert all(reason.effect == 0 for reason in report.reasons)
    assert all(effect == 0 for effect in report.groups.values())


def test_only_the_first_words_of_a_long_text_count():
    long = next(case for case in FIXTURES if case["id"] == "long-machine")
    assert len(long["text"].split()) > ANALYZER.max_words
    assert ANALYZER.analyze(long["text"]).words == ANALYZER.max_words
    assert ANALYZER.analyze("Мама мыла раму.").words == 3


def test_an_empty_text_is_refused():
    for blank in ("", "  \n", None):
        try:
            ANALYZER.analyze(blank)
        except ValueError:
            continue
        raise AssertionError(f"{blank!r} was accepted")


def test_the_model_file_describes_the_model_it_holds():
    meta = ANALYZER.meta
    assert meta["columns"] == [name for _, name, _ in describe_features(DEFAULT_GROUPS)]
    assert meta["groups"] == [group for group, _, _ in describe_features(DEFAULT_GROUPS)]
    assert len(meta["baseline"]) == 66
    assert meta["positive_class"] == "ai" and meta["max_words"] == 500
    assert 0.85 < meta["test_metrics"]["accuracy"] < 0.95 and meta["test_metrics"]["n"] == 52521
    assert meta["source"]["dataset"]["revision"]


def test_the_trees_are_walked_like_scikit_learn_does():
    # two stumps: x0 <= 0.5 gives -1 else +2; x1 <= 10 gives +0.5 else -0.5; log-odds start at 0.25
    boosting = Boosting(
        feature=[[0, 0, 0], [1, 0, 0]],
        threshold=[[0.5, 0, 0], [10.0, 0, 0]],
        left=[[1, 0, 0], [1, 0, 0]],
        right=[[2, 0, 0], [2, 0, 0]],
        value=[[0, -1.0, 2.0], [0, 0.5, -0.5]],
        is_leaf=[[False, True, True], [False, True, True]],
        base=0.25,
        depth=1,
    )
    rows = [[0.3, 5], [0.5, 11], [0.7, 11], [0.7, 3]]  # a value equal to the threshold goes left
    assert np.allclose(boosting.raw(rows), [-0.25, -1.25, 1.75, 2.75])
    assert np.allclose(boosting.proba(rows), 1 / (1 + np.exp(-np.array([-0.25, -1.25, 1.75, 2.75]))))
