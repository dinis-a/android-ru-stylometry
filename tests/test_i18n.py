"""Tests for the UI texts. Run with `python run_tests.py` (pytest works too)."""

import json
import sys
from pathlib import Path
from string import Formatter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from i18n import (  # noqa: E402
    DEFAULT_LANGUAGE,
    HOW_STEPS,
    LANGUAGES,
    LIMITS,
    TEXTS,
    format_feature,
    format_number,
    format_percent,
    pick_language,
)

META = json.loads((ROOT / "stylometry" / "model.json").read_text(encoding="utf-8"))


def placeholders(text):
    return {name for _, name, _, _ in Formatter().parse(text) if name is not None}


def test_every_language_has_texts():
    assert set(TEXTS) == set(LANGUAGES)
    assert DEFAULT_LANGUAGE in LANGUAGES


def test_languages_have_the_same_keys():
    reference = set(TEXTS[DEFAULT_LANGUAGE])
    for lang, texts in TEXTS.items():
        assert set(texts) == reference, (lang, reference ^ set(texts))


def test_languages_have_the_same_placeholders():
    # a text is filled in with str.format: a placeholder missing from one language would show up raw
    reference = TEXTS[DEFAULT_LANGUAGE]
    for lang, texts in TEXTS.items():
        for key, text in texts.items():
            assert placeholders(text) == placeholders(reference[key]), (lang, key)


def test_no_text_is_empty():
    for lang, texts in TEXTS.items():
        for key, text in texts.items():
            assert text, (lang, key)


def test_other_languages_are_translated():
    # a text copied from the default language is almost surely a forgotten translation
    reference = TEXTS[DEFAULT_LANGUAGE]
    for lang, texts in TEXTS.items():
        if lang != DEFAULT_LANGUAGE:
            assert [key for key, text in texts.items() if text == reference[key]] == [], lang


def test_every_feature_and_group_of_the_stylometric_model_has_a_label():
    groups = set(META["groups"])
    for lang, texts in TEXTS.items():
        for name in META["columns"]:
            assert f"feat_{name}" in texts, (lang, name)
        for group in groups:
            assert f"group_{group}" in texts, (lang, group)


def test_no_label_is_left_for_a_feature_the_model_does_not_have():
    for lang, texts in TEXTS.items():
        labelled = {key[len("feat_") :] for key in texts if key.startswith("feat_")}
        assert labelled == set(META["columns"]), (lang, labelled ^ set(META["columns"]))
        assert {key[len("group_") :] for key in texts if key.startswith("group_")} == set(META["groups"])


def test_steps_and_limits_are_numbered_without_gaps():
    for keys, prefix in ((HOW_STEPS, "how_step_"), (LIMITS, "limit_")):
        assert keys
        assert keys == tuple(f"{prefix}{number}" for number in range(1, len(keys) + 1))


def test_pick_language_takes_the_first_supported_one():
    assert pick_language(["de", "en", "ru"]) == "en"
    assert pick_language(["ru_RU"]) == "ru"
    assert pick_language(["EN-us"]) == "en"
    assert pick_language(["de", "fr"]) == DEFAULT_LANGUAGE
    assert pick_language([]) == DEFAULT_LANGUAGE


def test_numbers_use_the_decimal_mark_of_the_language():
    assert format_number(1234.5, "en", 2) == "1234.50"
    assert format_number(1234.5, "ru", 2) == "1234,50"


def test_probabilities_are_never_shown_as_certain():
    assert format_percent(0.004, "en") == "less than 1%"
    assert format_percent(0.9999, "ru") == "больше 99%"
    assert format_percent(0.5, "en") == "50%"
    assert format_percent(0.8731, "ru") == "87%"


def test_features_are_shown_in_their_own_units():
    assert format_feature("conj_ratio", 0.116, "en") == "11.6%"
    assert format_feature("case_gent_share", 0.0544, "ru") == "5,4%"
    assert format_feature("avg_word_len", 6.157, "en") == "6.16"
    assert format_feature("mtld", 85.34, "ru") == "85,3"
    assert format_feature("comma_per100w", 9.09, "en") == "9.09"
