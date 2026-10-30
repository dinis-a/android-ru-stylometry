"""A second opinion on a text from interpretable stylometric features, with the reasons for it.

The text is turned into the 66 features of ru-stylometry and a gradient-boosting model, trained
on them, says how likely the text is machine-made. The reasons follow ``explain_row`` of
ru-stylometry: a feature is replaced by its typical value (the training median) and the fall of
the log-odds of "machine" is its effect. Positive effects push towards "machine", negative ones
towards "human". The effects are not additive: correlated features share the credit, so the
effect of a whole group of features is measured apart.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from stylometry.boost import Boosting
from stylometry.lib import extract_features

CLIP = 1e-6  # as in ru-stylometry: probabilities are clipped before the log-odds are taken


@dataclass
class Reason:
    feature: str
    group: str
    value: float  # in this text
    typical: float  # median over the training texts: what the effect is measured against
    human: float  # median over the human texts
    machine: float  # median over the machine texts
    effect: float  # fall of the log-odds of "machine" when the feature is set to `typical`


@dataclass
class StyleReport:
    p_ai: float
    reasons: list  # every feature, the strongest effect first
    groups: dict  # group name -> its effect, the strongest first
    words: int  # words analysed: only the first `max_words` of a long text count


def log_odds(p):
    p = np.clip(p, CLIP, 1.0 - CLIP)
    return np.log(p / (1.0 - p))


class StyleAnalyzer:
    """Loads the model once; ``analyze`` costs a few milliseconds plus the morphology of the text."""

    def __init__(self, folder=None):
        folder = Path(folder) if folder is not None else Path(__file__).resolve().parent
        self.meta = json.loads((folder / "model.json").read_text(encoding="utf-8"))
        self.columns = list(self.meta["columns"])
        self.group_of = list(self.meta["groups"])
        self.max_words = int(self.meta["max_words"])
        self.baseline = np.asarray(self.meta["baseline"], dtype=np.float64)
        self.human = np.asarray(self.meta["median_human"], dtype=np.float64)
        self.machine = np.asarray(self.meta["median_machine"], dtype=np.float64)
        with np.load(folder / "model.npz") as arrays:
            self.boosting = Boosting(
                arrays["feature"],
                arrays["threshold"],
                arrays["left"],
                arrays["right"],
                arrays["value"],
                arrays["is_leaf"],
                self.meta["base"],
                self.meta["depth"],
            )
        self.group_names = list(dict.fromkeys(self.group_of))

    def features(self, text):
        """The feature vector of a text in the order of the model's columns."""
        values = extract_features(text, max_words=self.max_words)
        return np.array([values[name] for name in self.columns], dtype=np.float64)

    def analyze(self, text):
        """The probability of machine text and the reasons for it; ValueError for an empty text."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("the text is empty")
        row = self.features(text)
        n = len(self.columns)
        # row 0 is the text itself, then one row per feature and one per group with the
        # feature(s) replaced by their typical value
        variants = np.tile(row, (1 + n + len(self.group_names), 1))
        for i in range(n):
            variants[1 + i, i] = self.baseline[i]
        members = np.asarray(self.group_of)
        for j, group in enumerate(self.group_names):
            columns = np.flatnonzero(members == group)
            variants[1 + n + j, columns] = self.baseline[columns]
        probabilities = self.boosting.proba(variants)
        odds = log_odds(probabilities)
        effects = odds[0] - odds[1 : 1 + n]
        reasons = [
            Reason(
                self.columns[i],
                self.group_of[i],
                float(row[i]),
                float(self.baseline[i]),
                float(self.human[i]),
                float(self.machine[i]),
                float(effects[i]),
            )
            for i in np.argsort(-np.abs(effects), kind="stable")
        ]
        groups = {group: float(odds[0] - odds[1 + n + j]) for j, group in enumerate(self.group_names)}
        groups = dict(sorted(groups.items(), key=lambda item: -abs(item[1])))
        words = min(len(text.split()), self.max_words)
        return StyleReport(float(probabilities[0]), reasons, groups, words)

    def warm_up(self):
        """Load the morphology dictionaries now instead of during the first analysis."""
        self.features("Мама мыла раму.")
