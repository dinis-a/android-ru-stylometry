"""The feature extractor of ru-stylometry 0.1.1 (MIT, see LICENSE) without its scikit-learn parts.

Copied from https://github.com/dinis-a/ru-stylometry: the modules that need nothing but the
standard library and pymorphy3, because a phone cannot install scikit-learn. The changes are the
package name in the imports and the path to the dictionaries of pymorphy3 (_morph.py). To update,
copy the same files from a newer release and make these two changes again.
"""

from stylometry.lib.features import (
    ALL_GROUPS,
    DEFAULT_GROUPS,
    describe_features,
    extract_features,
    feature_names,
)

__all__ = ["ALL_GROUPS", "DEFAULT_GROUPS", "describe_features", "extract_features", "feature_names"]
