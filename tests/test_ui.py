"""Tests for the screens, driven through a stand-in for the Flet page. Run with `python run_tests.py`."""

import asyncio
import logging
import sys
from pathlib import Path

import msgpack

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import flet as ft  # noqa: E402
from flet.messaging.protocol import configure_encode_object_for_msgpack  # noqa: E402

import samples  # noqa: E402
import ui  # noqa: E402
from i18n import LANGUAGES, TEXTS  # noqa: E402
from ru_detector import Detector  # noqa: E402
from stylometry import StyleAnalyzer  # noqa: E402
from tests.stubs import StubPage  # noqa: E402
from verdict import SHORT_WORDS  # noqa: E402

logging.getLogger("ui").setLevel(logging.CRITICAL)  # the tests of failures log on purpose

DETECTOR = Detector()
ANALYZER = StyleAnalyzer()
LONG_MACHINE = samples.MACHINE
SHORT_TEXT = "Привет, как дела у тебя сегодня?"


class FakeDetector:
    """Answers with a fixed probability; `config` is what the About page reads."""

    threshold = 0.5
    config = {"base_model": "fake/model", "test_metrics": {"accuracy": 0.9}}

    def __init__(self, p_ai):
        self.p_ai = p_ai

    def predict(self, text):
        # the self-check sends two different texts and expects different answers
        p = self.p_ai(text) if callable(self.p_ai) else self.p_ai
        return {"label": "ai", "p_ai": p, "tokens": max(1, len(text) // 4), "truncated": False}


def make_app(detector=DETECTOR, analyzer=ANALYZER, lang="ru", saved=None, clipboard=None):
    page = StubPage()
    app = ui.App(
        page, detector, analyzer, lang, save_language=saved.append if saved is not None else None, read_clipboard=clipboard
    )
    return app, page


def type_text(app, text):
    app.field.value = text
    app.on_change(None)


def texts_in(control):
    """Every string shown under a control."""
    found = []
    for attr in ("value", "content", "label", "hint_text"):
        value = getattr(control, attr, None)
        if isinstance(value, str):
            found.append(value)
    for child in getattr(control, "controls", None) or []:
        found += texts_in(child)
    content = getattr(control, "content", None)
    if content is not None and not isinstance(content, str):
        found += texts_in(content)
    return found


def test_the_app_builds_and_its_controls_can_be_sent_to_the_client():
    app, page = make_app()
    type_text(app, LONG_MACHINE)
    app.check()  # the card with the reasons is the largest tree the client gets
    assert app.result.visible
    encode = configure_encode_object_for_msgpack(ft.BaseControl)
    for root in (page.controls, page.appbar, page.navigation_bar, app.result):
        assert msgpack.packb(root, default=encode)


def test_the_page_is_set_up_like_the_other_apps():
    app, page = make_app()
    assert page.title == TEXTS["ru"]["window_title"]
    assert page.theme_mode == ft.ThemeMode.DARK
    assert page.appbar is app.top_bar and page.navigation_bar is app.nav_bar
    assert app.check_card.visible and not app.info_card.visible
    assert [d.label for d in app.nav_bar.destinations] == [TEXTS["ru"]["nav_check"], TEXTS["ru"]["nav_info"]]


def test_a_machine_text_gets_a_verdict_and_its_reasons():
    app, _ = make_app()
    type_text(app, LONG_MACHINE)
    app.check()
    assert app.title.value == TEXTS["ru"]["verdict_ai"]
    assert app.bar.visible and app.bar.value > 0.99
    assert "больше 99%" in app.detail.value
    assert app.style_box.visible
    shown = " ".join(texts_in(app.style_body))
    assert TEXTS["ru"]["style_probability"].split("{")[0] in shown
    assert TEXTS["ru"]["reasons_title"] in shown and TEXTS["ru"]["groups_title"] in shown
    # five reasons, each with the three values to compare
    assert shown.count(TEXTS["ru"]["reason_values"].split("{")[0]) == ui.TOP_REASONS
    assert not app.check_button.disabled and not app.spinner.visible


def test_a_human_text_gets_a_verdict():
    app, _ = make_app()
    type_text(app, samples.HUMAN)
    app.check()
    assert app.title.value == TEXTS["ru"]["verdict_human"]
    assert app.bar.value < 0.25


def test_an_empty_field_asks_for_a_text():
    app, _ = make_app()
    for blank in (None, "", "  \n "):
        app.field.value = blank
        app.check()
        assert app.title.value == TEXTS["ru"]["verdict_empty"]
        assert not app.bar.visible and not app.style_box.visible


def test_a_short_text_is_still_checked_but_with_a_warning():
    app, _ = make_app()
    type_text(app, SHORT_TEXT)
    assert app.counter.value == TEXTS["ru"]["counter_short"].format(n=6)
    app.check()
    assert app.title.value in (TEXTS["ru"][f"verdict_{kind}"] for kind in ("ai", "human", "unsure"))
    assert app.bar.visible
    shown = " ".join(texts_in(app.notes))
    assert TEXTS["ru"]["note_short"].format(n=SHORT_WORDS) in shown


def test_an_english_text_gets_no_verdict_and_no_reasons():
    app, _ = make_app()
    type_text(app, "The quick brown fox jumps over the lazy dog and keeps running through the forest.")
    app.check()
    assert app.title.value == TEXTS["ru"]["verdict_foreign"]
    assert not app.bar.visible and not app.style_box.visible


def test_editing_the_text_hides_the_old_verdict():
    app, _ = make_app()
    type_text(app, LONG_MACHINE)
    app.check()
    assert app.result.visible
    type_text(app, LONG_MACHINE + " ещё")
    assert not app.result.visible


def test_clear_empties_the_field_and_the_card():
    app, _ = make_app()
    type_text(app, LONG_MACHINE)
    app.check()
    app.clear()
    assert app.field.value == "" and not app.result.visible
    assert app.counter.value == TEXTS["ru"]["counter"].format(n=0)


def test_paste_replaces_the_text_with_the_clipboard_and_leaves_the_checking_to_the_user():
    async def clipboard():
        return "Новый текст из буфера обмена."

    app, _ = make_app(clipboard=clipboard)
    type_text(app, LONG_MACHINE)
    app.check()
    assert app.result.visible
    asyncio.run(app.paste())
    assert app.field.value == "Новый текст из буфера обмена."
    assert app.counter.value == TEXTS["ru"]["counter_short"].format(n=5)
    assert not app.result.visible  # the verdict on show was for the old text, and nothing is checked yet


def test_an_empty_or_unreadable_clipboard_is_told_and_the_text_stays():
    async def nothing():
        return None

    async def blank():
        return " \n "

    async def broken():
        raise RuntimeError("no access to the clipboard")

    for read in (nothing, blank, broken, None):  # None: the app was started without a clipboard
        app, _ = make_app(clipboard=read)
        type_text(app, SHORT_TEXT)
        asyncio.run(app.paste())
        assert app.field.value == SHORT_TEXT
        assert app.title.value == TEXTS["ru"]["verdict_clipboard"]
        assert not app.bar.visible and not app.style_box.visible


def test_the_paste_button_follows_the_language():
    app, _ = make_app()
    assert app.paste_button.content == TEXTS["ru"]["button_paste"]
    app.set_language("en")
    assert app.paste_button.content == TEXTS["en"]["button_paste"]


def test_the_examples_fill_the_field_and_check_it():
    app, _ = make_app()
    app.use_sample(samples.MACHINE)
    assert app.field.value == samples.MACHINE
    assert app.title.value == TEXTS["ru"]["verdict_ai"]
    app.use_sample(samples.HUMAN)
    assert app.title.value == TEXTS["ru"]["verdict_human"]


def test_a_failing_detector_shows_an_error_and_frees_the_button():
    class Raising(FakeDetector):
        def predict(self, text):
            raise RuntimeError("boom")

    app, _ = make_app(Raising(0.5), analyzer=None)  # the self-check at the start fails too
    assert app.banner_box.visible
    type_text(app, LONG_MACHINE)
    app.check()
    assert app.title.value == TEXTS["ru"]["verdict_error"]
    assert not app.check_button.disabled and not app.spinner.visible


def test_a_broken_stylometry_leaves_the_neural_answer_and_says_why():
    class Broken:
        meta = ANALYZER.meta

        def analyze(self, text):
            raise ModuleNotFoundError("No module named 'pymorphy3'")

        def warm_up(self):
            raise ModuleNotFoundError("No module named 'pymorphy3'")

    app, _ = make_app(analyzer=Broken())
    type_text(app, LONG_MACHINE)
    app.check()
    assert app.title.value == TEXTS["ru"]["verdict_ai"]
    shown = " ".join(texts_in(app.style_body))
    assert "pymorphy3" in shown and TEXTS["ru"]["style_unavailable"].split("{")[0] in shown


def test_without_a_stylometric_model_there_are_no_reasons():
    app, _ = make_app(analyzer=None)
    type_text(app, LONG_MACHINE)
    app.check()
    assert app.title.value == TEXTS["ru"]["verdict_ai"] and not app.style_box.visible


def test_a_model_that_answers_everything_alike_raises_the_alarm():
    app, _ = make_app(FakeDetector(0.7), analyzer=None)
    assert app.banner_box.visible
    assert TEXTS["ru"]["banner_broken"].split("{")[0] in app.banner.value
    healthy, _ = make_app()
    assert not healthy.banner_box.visible


def test_switching_the_language_changes_every_text_and_is_remembered():
    saved = []
    app, _ = make_app(saved=saved)
    type_text(app, LONG_MACHINE)
    app.check()
    app.set_language("en")
    assert saved == ["en"]
    assert app.title.value == TEXTS["en"]["verdict_ai"]
    assert app.field.label == TEXTS["en"]["field_label"]
    assert app.check_button.content == TEXTS["en"]["button_check"]
    assert [d.label for d in app.nav_bar.destinations] == [TEXTS["en"]["nav_check"], TEXTS["en"]["nav_info"]]
    assert "more than 99%" in app.detail.value
    shown = " ".join(texts_in(app.style_body))
    assert TEXTS["en"]["reasons_title"] in shown and TEXTS["en"]["reasons_title"] != TEXTS["ru"]["reasons_title"]
    assert app.page.title == TEXTS["en"]["window_title"]
    app.set_language("ru")
    assert saved == ["en", "ru"] and app.title.value == TEXTS["ru"]["verdict_ai"]


def test_every_language_button_works_and_the_active_one_is_marked():
    app, _ = make_app()
    assert set(app.language_buttons) == set(LANGUAGES)
    ru, en = app.language_buttons["ru"], app.language_buttons["en"]
    assert ru.style.bgcolor == ui.ACCENT and en.style.bgcolor == ui.SURFACE
    app.set_language("en")
    assert en.style.bgcolor == ui.ACCENT and ru.style.bgcolor == ui.SURFACE


def test_the_navigation_bar_shows_one_page_at_a_time():
    app, page = make_app()

    class Event:
        def __init__(self, index):
            self.control = type("Bar", (), {"selected_index": index})()

    app.show_page(Event(1))
    assert app.info_card.visible and not app.check_card.visible
    app.show_page(Event(0))
    assert app.check_card.visible and not app.info_card.visible
    assert page.tasks  # the page scrolls back to its top


def test_the_about_page_states_the_accuracy_of_both_models():
    app, _ = make_app()
    shown = " ".join(texts_in(app.info_card))
    assert "94,2%" in shown  # the neural model: config.json of ru_detector
    assert format(100 * ANALYZER.meta["test_metrics"]["accuracy"], ".1f").replace(".", ",") + "%" in shown
    assert ui.APP_VERSION in shown
    app.set_language("en")
    assert "94.2%" in " ".join(texts_in(app.info_card))


def test_the_cards_follow_the_width_of_the_screen():
    app, page = make_app()
    page.width = 400
    app.fit_cards()
    assert app.check_card.width == app.info_card.width == 400 - 2 * ui.SCREEN_MARGIN
    page.width = 2000
    app.fit_cards()
    assert app.check_card.width == ui.MAX_CARD_WIDTH
    page.width = 100
    app.fit_cards()
    assert app.check_card.width == ui.MIN_CARD_WIDTH


def test_signed_numbers_use_the_decimal_mark_of_the_language():
    assert ui.signed(1.94, "en") == "+1.9"
    assert ui.signed(-0.44, "ru") == "−0,4"
    assert ui.signed(0.0, "en") == "0.0"


def test_agreement_of_the_two_models():
    assert ui.agreement("ai", "ai") == "agree_yes"
    assert ui.agreement("human", "human") == "agree_yes"
    assert ui.agreement("ai", "human") == "agree_no"
    assert ui.agreement("unsure", "ai") == "agree_partial"
    assert ui.agreement("human", "unsure") == "agree_partial"
