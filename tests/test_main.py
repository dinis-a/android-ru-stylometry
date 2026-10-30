"""Tests for the entry point: the choice of the language and the start of the app.

Run with `python run_tests.py` (pytest works too).
"""

import asyncio
import logging
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main as entry  # noqa: E402
from i18n import TEXTS  # noqa: E402
from tests.stubs import StubPage  # noqa: E402

logging.getLogger("main").setLevel(logging.CRITICAL)  # the tests of failures log on purpose


class Prefs:
    def __init__(self, value=None, fails=False):
        self.value, self.fails = value, fails

    async def get(self, key):
        if self.fails:
            raise RuntimeError("the store is broken")
        return self.value


class Page(StubPage):
    """A page that knows the languages of the device."""

    def __init__(self, locales=(), fails=False):
        super().__init__()
        self.locales, self.fails = locales, fails

    async def get_device_info(self):
        if self.fails:
            raise RuntimeError("no device info")
        return SimpleNamespace(locales=[SimpleNamespace(language_code=code) for code in self.locales])


@contextmanager
def storage(prefs):
    """main() makes its own SharedPreferences, which need a running page: swap in a stand-in."""
    original = entry.ft.SharedPreferences
    entry.ft.SharedPreferences = lambda: prefs
    try:
        yield
    finally:
        entry.ft.SharedPreferences = original


@contextmanager
def clipboard_of(service):
    """main() makes its own Clipboard, which needs a running page: swap in a stand-in."""
    original = entry.ft.Clipboard
    entry.ft.Clipboard = lambda: service
    try:
        yield
    finally:
        entry.ft.Clipboard = original


def run(coroutine):
    return asyncio.run(coroutine)


def test_the_saved_language_is_used_when_it_is_one_of_ours():
    assert run(entry.saved_language(Prefs("en"))) == "en"
    assert run(entry.saved_language(Prefs("ru"))) == "ru"


def test_a_saved_language_that_does_not_exist_is_ignored():
    for value in (None, "", "de", 5):
        assert run(entry.saved_language(Prefs(value))) is None


def test_a_broken_store_does_not_stop_the_app():
    assert run(entry.saved_language(Prefs("en", fails=True))) is None


def test_the_languages_of_the_device_come_in_order_of_preference():
    assert run(entry.device_languages(Page(["de", "en", "ru"]))) == ["de", "en", "ru"]
    assert run(entry.device_languages(Page(fails=True))) == []


def test_the_app_starts_in_the_language_of_the_device_when_none_is_saved():
    page = Page(["en-US"])
    with storage(Prefs(None)):
        run(entry.main(page))
    assert page.title == TEXTS["en"]["window_title"] and page.controls


def test_the_saved_language_beats_the_language_of_the_device():
    page = Page(["en"])
    with storage(Prefs("ru")):
        run(entry.main(page))
    assert page.title == TEXTS["ru"]["window_title"]


def test_a_device_in_another_language_gets_russian():
    page = Page(["de"])
    with storage(Prefs(None)):
        run(entry.main(page))
    assert page.title == TEXTS["ru"]["window_title"]


def test_the_choice_of_the_user_is_stored():
    stored = []

    class Remembering(Prefs):
        async def set(self, key, value):
            stored.append((key, value))

    page = Page(["ru"])
    with storage(Remembering(None)):
        run(entry.main(page))
    assert page.tasks == []  # opening the app stores nothing
    page.on_resize.__self__.set_language("en")  # the user taps EN; on_resize is a method of the App
    handler, args, _ = page.tasks[-1]
    run(handler(*args))
    assert stored == [(entry.LANGUAGE_KEY, "en")]


def test_the_paste_button_reads_the_clipboard_of_the_device():
    class Clipboard:
        async def get(self):
            return "Скопированный текст"

    page = Page(["ru"])
    with storage(Prefs(None)), clipboard_of(Clipboard()):
        run(entry.main(page))
    app = page.on_resize.__self__  # on_resize is a method of the App
    run(app.paste())
    assert app.field.value == "Скопированный текст"


def test_without_a_model_the_screen_says_so_instead_of_staying_blank():
    original = entry.detector, entry.load_error
    entry.detector, entry.load_error = None, FileNotFoundError("model.onnx")
    page = Page()
    try:
        with storage(Prefs("en")):
            run(entry.main(page))
    finally:
        entry.detector, entry.load_error = original
    assert len(page.controls) == 1
    assert page.controls[0].value == "Could not load the model: model.onnx"
    assert not hasattr(page, "appbar")


def test_the_shipped_models_load():
    assert entry.detector is not None and entry.analyzer is not None
