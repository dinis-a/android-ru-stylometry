import logging

import flet as ft

from i18n import TEXTS, pick_language
from ru_detector import Detector
from stylometry import StyleAnalyzer
from ui import App

logger = logging.getLogger(__name__)

LANGUAGE_KEY = "language"  # where the user's choice of language is stored (SharedPreferences)

load_error = None
try:
    detector = Detector()  # the model is loaded once, at the start of the app
except Exception as error:  # say what is wrong on the screen instead of showing a blank page
    detector, load_error = None, error

try:
    analyzer = StyleAnalyzer()  # the reasons; without them the app still gives its answer
except Exception:
    logger.warning("could not load the stylometric model", exc_info=True)
    analyzer = None


async def saved_language(prefs: ft.SharedPreferences) -> str | None:
    """The language the user picked in an earlier session, if any."""
    try:
        code = await prefs.get(LANGUAGE_KEY)
    except Exception:  # the choice is a convenience: a broken store must not stop the app
        logger.warning("could not read the saved language", exc_info=True)
        return None
    return code if isinstance(code, str) and code in TEXTS else None


async def device_languages(page: ft.Page) -> list[str]:
    """Language codes the device is set to, the most preferred first."""
    try:
        info = await page.get_device_info()
    except Exception:  # without it the default language will do
        logger.warning("could not read the device languages", exc_info=True)
        return []
    return [locale.language_code for locale in info.locales] if info else []


async def main(page: ft.Page):
    prefs = ft.SharedPreferences()
    lang = await saved_language(prefs) or pick_language(await device_languages(page))
    if detector is None:
        page.add(ft.Text(TEXTS[lang]["banner_load"].format(error=load_error), selectable=True))
        return
    App(
        page,
        detector,
        analyzer,
        lang,
        save_language=lambda code: page.run_task(prefs.set, LANGUAGE_KEY, code),
    )


if __name__ == "__main__":
    ft.run(main)
