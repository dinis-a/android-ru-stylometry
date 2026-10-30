"""Predictions of scikit-learn's HistGradientBoostingClassifier with numpy alone.

A phone cannot install scikit-learn, so tools/export_stylometry.py copies the trees of the trained
model into arrays and this module walks them. Only what that model uses is supported: two classes,
the log-loss, splits on numeric features and no missing values.
"""

import numpy as np


class Boosting:
    """Trees as padded arrays: a row per tree, a column per node, node 0 the root.

    ``feature``, ``threshold``, ``left`` and ``right`` describe the splits (a row goes left when
    its feature is at most the threshold), ``value`` is what a leaf adds to the log-odds and
    ``base`` is the log-odds before any tree.
    """

    def __init__(self, feature, threshold, left, right, value, is_leaf, base, depth):
        self.feature = np.asarray(feature, dtype=np.int64)
        self.threshold = np.asarray(threshold, dtype=np.float64)
        self.left = np.asarray(left, dtype=np.int64)
        self.right = np.asarray(right, dtype=np.int64)
        self.value = np.asarray(value, dtype=np.float64)
        self.is_leaf = np.asarray(is_leaf, dtype=bool)
        self.base = float(base)
        self.depth = int(depth)  # the longest path from a root to a leaf

    def raw(self, rows):
        """Log-odds of the positive class for every row of an (n_rows, n_features) matrix."""
        rows = np.asarray(rows, dtype=np.float64)
        tree = np.arange(len(self.feature))[:, None]
        row = np.arange(len(rows))[None, :]
        node = np.zeros((len(self.feature), len(rows)), dtype=np.int64)
        for _ in range(self.depth):
            go_left = rows[row, self.feature[tree, node]] <= self.threshold[tree, node]
            child = np.where(go_left, self.left[tree, node], self.right[tree, node])
            node = np.where(self.is_leaf[tree, node], node, child)
        return self.base + self.value[tree, node].sum(axis=0)

    def proba(self, rows):
        """Probability of the positive class for every row."""
        return 1.0 / (1.0 + np.exp(-self.raw(rows)))
