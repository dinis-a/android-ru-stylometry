"""The screens of the app: the check page, the About page, the top bar and the navigation bar."""

import logging

import flet as ft

import samples
from i18n import (
    HOW_STEPS,
    LANGUAGES,
    LIMITS,
    TEXTS,
    format_number,
    format_percent,
)
from verdict import SHORT_WORDS, assess, count_words, decide, health_check

log = logging.getLogger(__name__)

APP_NAME = "AITrace"  # the name under the launcher icon (pyproject.toml) and in RuStore; not translated
APP_VERSION = "0.2.0"  # the same as in pyproject.toml; a test compares them

ACCENT = ft.Colors.TEAL
MUTED = ft.Colors.WHITE_70
SURFACE = ft.Colors.WHITE_10
OUTLINE = ft.Colors.WHITE_30
SCREEN_MARGIN = 12
MIN_CARD_WIDTH = 280
MAX_CARD_WIDTH = 560
FALLBACK_SCREEN_WIDTH = 360  # until the client reports its real size
CARD_PADDING = 16
BAR_HEIGHT = 8
TOP_REASONS = 5  # features listed under "main reasons"

# kind of verdict: icon, colour
LOOKS = {
    "ai": (ft.Icons.SMART_TOY, ft.Colors.DEEP_ORANGE_400),
    "human": (ft.Icons.PERSON, ft.Colors.GREEN_400),
    "unsure": (ft.Icons.HELP_OUTLINE, ft.Colors.BLUE_GREY_200),
    "foreign": (ft.Icons.TRANSLATE, ft.Colors.BLUE_GREY_200),
    "empty": (ft.Icons.TEXT_SNIPPET, ft.Colors.BLUE_GREY_200),
    "clipboard": (ft.Icons.CONTENT_PASTE, ft.Colors.BLUE_GREY_200),
    "error": (ft.Icons.ERROR_OUTLINE, ft.Colors.RED_300),
}
AGREEMENT_COLOURS = {
    "agree_yes": ft.Colors.GREEN_400,
    "agree_no": ft.Colors.AMBER_400,
    "agree_partial": MUTED,
}


def signed(value, lang):
    """A number with its sign, one decimal: '+1.9', '−0.4'."""
    sign = "+" if value > 0 else "−" if value < 0 else ""
    return sign + format_number(abs(value), lang, 1)


def agreement(neural, style):
    """Text key for how the verdict of the neural model and that of stylometry relate."""
    if "unsure" in (neural, style):
        return "agree_partial"
    return "agree_yes" if neural == style else "agree_no"


class App:
    """Puts the app on a Flet page and keeps its controls, so that tests can drive them."""

    def __init__(self, page, detector, analyzer=None, lang="ru", save_language=None, read_clipboard=None):
        self.page = page
        self.detector = detector
        self.analyzer = analyzer
        self.lang = lang
        self.save_language = save_language  # called with the code when the user picks a language
        self.read_clipboard = read_clipboard  # an async function that gives the text on the clipboard
        self.bindings = []  # (control, attribute, function giving the text): see `bind`
        self.verdict = None  # what the card shows: a Verdict ...
        self.message = None  # ... or "empty" / "error"
        self.style = None  # None, "loading", a StyleReport or ("error", text)
        self.problem = health_check(detector)
        if self.problem:
            log.error("the model gives one answer to different texts: %s", self.problem)

        self.build_check_page()
        self.build_info_page()
        self.build_bars()

        page.theme_mode = ft.ThemeMode.DARK
        page.theme = page.dark_theme = ft.Theme(color_scheme_seed=ACCENT)
        page.bgcolor = ft.Colors.BLACK
        page.padding = 0
        page.scroll = ft.ScrollMode.AUTO
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.appbar = self.top_bar
        page.navigation_bar = self.nav_bar
        page.on_resize = self.fit_cards
        # spacing=0: the page that is hidden must not leave a gap above or below the shown one
        page.add(
            ft.SafeArea(
                content=ft.Column([self.check_card, self.info_card], spacing=0),
                minimum_padding=SCREEN_MARGIN,
            )
        )
        self.fit_cards()
        self.apply_language()
        if analyzer is not None:
            page.run_thread(self.warm_up)  # the morphology dictionaries load while the user types

    # ---- texts -----------------------------------------------------------
    def tr(self, key, **values):
        return TEXTS[self.lang][key].format(**values)

    def bind(self, control, text, attr="value"):
        """Show `text()` in `control.<attr>` now and after every change of the language."""
        self.bindings.append((control, attr, text))
        setattr(control, attr, text())
        return control

    def label(self, key, **style):
        """A Text that shows the text `key`."""
        return self.bind(ft.Text(**style), lambda: self.tr(key))

    def percent(self, p):
        return format_percent(p, self.lang)

    def accuracy(self, source):
        value = source.get("test_metrics", {}).get("accuracy") if source else None
        return format_number(100 * value, self.lang, 1) + "%" if value else "—"

    def apply_language(self):
        """Show every text in the current language."""
        for control, attr, text in self.bindings:
            setattr(control, attr, text())
        self.page.title = self.tr("window_title")
        # the system's own widgets (the text-selection menu) follow the app's language, not the phone's
        self.page.locale_configuration = ft.LocaleConfiguration(
            supported_locales=[ft.Locale(code) for code in LANGUAGES],
            current_locale=ft.Locale(self.lang),
        )
        for code, button in self.language_buttons.items():
            button.style = self.toggle_style(code == self.lang)
        self.update_counter()
        self.banner.value = self.tr("banner_broken", problem=self.problem) if self.problem else ""
        self.banner_box.visible = bool(self.problem)
        self.render()
        self.page.update()

    def set_language(self, code):
        self.lang = code
        self.apply_language()
        if self.save_language:
            self.save_language(code)

    def toggle_style(self, active):
        return ft.ButtonStyle(
            bgcolor=ACCENT if active else SURFACE, color=ft.Colors.WHITE if active else MUTED
        )

    # ---- layout ----------------------------------------------------------
    def page_card(self, *controls):
        """The outlined panel a page is drawn on; `fit_cards` keeps its width in step with the screen."""
        return ft.Container(
            width=FALLBACK_SCREEN_WIDTH - 2 * SCREEN_MARGIN,
            padding=CARD_PADDING,
            border_radius=24,
            bgcolor=ft.Colors.BLACK,
            border=ft.Border.all(1, SURFACE),
            content=ft.Column(
                list(controls), spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH
            ),
        )

    def heading(self, key):
        return self.label(key, size=18, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE)

    def fit_cards(self, e=None):
        screen = self.page.width or FALLBACK_SCREEN_WIDTH
        width = max(MIN_CARD_WIDTH, min(screen - 2 * SCREEN_MARGIN, MAX_CARD_WIDTH))
        for card in (self.check_card, self.info_card):
            card.width = width

    def build_check_page(self):
        # the frame has to be drawn: on the black page an empty field is otherwise a hole with a word in it
        self.field = ft.TextField(
            multiline=True,
            min_lines=6,
            max_lines=12,
            border_radius=12,
            border_color=OUTLINE,
            focused_border_color=ACCENT,
            align_label_with_hint=True,
            on_change=self.on_change,
        )
        self.bind(self.field, lambda: self.tr("field_label"), attr="label")
        self.bind(self.field, lambda: self.tr("field_hint"), attr="hint_text")
        self.counter = self.bind(ft.Text(size=12, color=MUTED, expand=True), self.counter_text)
        self.paste_button = self.bind(
            ft.TextButton(icon=ft.Icons.CONTENT_PASTE, on_click=self.paste),
            lambda: self.tr("button_paste"),
            attr="content",
        )
        # the warning about a short text is long: the counter takes the room the button leaves and wraps
        status = ft.Row([self.counter, self.paste_button], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        self.check_button = self.bind(
            ft.Button(icon=ft.Icons.SEARCH, on_click=self.check),
            lambda: self.tr("button_check"),
            attr="content",
        )
        self.spinner = ft.ProgressRing(width=20, height=20, visible=False)
        examples = ft.Row(
            [
                self.label("examples", size=12, color=MUTED),
                self.bind(
                    ft.TextButton(on_click=lambda e: self.use_sample(samples.MACHINE)),
                    lambda: self.tr("example_machine"),
                    attr="content",
                ),
                self.bind(
                    ft.TextButton(on_click=lambda e: self.use_sample(samples.HUMAN)),
                    lambda: self.tr("example_human"),
                    attr="content",
                ),
            ],
            spacing=4,
            wrap=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        buttons = ft.Row(
            [
                self.check_button,
                self.bind(
                    ft.OutlinedButton(on_click=self.clear),
                    lambda: self.tr("button_clear"),
                    attr="content",
                ),
                self.spinner,
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.banner = ft.Text(color=ft.Colors.ON_ERROR_CONTAINER, size=13)
        self.banner_box = ft.Container(
            content=self.banner,
            visible=False,
            padding=12,
            border_radius=12,
            bgcolor=ft.Colors.ERROR_CONTAINER,
        )

        # the card with the verdict and the reasons for it
        self.icon = ft.Icon(icon=ft.Icons.HELP_OUTLINE, size=28)
        self.title = ft.Text(size=18, weight=ft.FontWeight.W_700, expand=True)
        self.detail = ft.Text(size=13, color=MUTED)
        self.bar = ft.ProgressBar(value=0, bar_height=10)
        self.notes = ft.Column(spacing=6)
        self.style_body = ft.Column(spacing=8, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        self.style_box = ft.Column(
            [
                ft.Divider(height=8, color=SURFACE),
                self.heading("style_title"),
                self.label("style_intro", size=12, color=MUTED),
                self.style_body,
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        self.result = ft.Container(
            visible=False,
            padding=CARD_PADDING,
            border_radius=16,
            bgcolor=SURFACE,
            content=ft.Column(
                [
                    ft.Row([self.icon, self.title], spacing=8),
                    self.detail,
                    self.bar,
                    self.notes,
                    self.style_box,
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )

        self.check_card = self.page_card(
            self.label("title", size=20, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
            self.label("subtitle", size=11, color=MUTED),
            ft.Divider(height=8, color=SURFACE),
            self.banner_box,
            self.field,
            status,
            buttons,
            examples,
            self.result,
        )

    def build_info_page(self):
        def step(number, key):
            return ft.Row(
                [
                    ft.Text(f"{number}.", size=13, color=ACCENT, weight=ft.FontWeight.W_600),
                    self.label(key, size=13, color=MUTED, expand=True),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )

        def bullet(key):
            text = self.bind(ft.Text(size=13, color=MUTED, expand=True), self.limit_text(key))
            return ft.Row(
                [ft.Text("•", size=13, color=ACCENT), text],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )

        neural = getattr(self.detector, "config", {})
        style = self.analyzer.meta if self.analyzer else None
        divider = lambda: ft.Divider(height=8, color=SURFACE)  # noqa: E731
        self.info_card = self.page_card(
            self.label("about_title", size=20, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
            self.label("about_text", size=13, color=MUTED),
            divider(),
            self.heading("how_title"),
            *(step(number, key) for number, key in enumerate(HOW_STEPS, start=1)),
            divider(),
            self.heading("models_title"),
            self.bind(
                ft.Text(size=13, color=MUTED),
                lambda: self.tr(
                    "model_neural",
                    base=neural.get("base_model", "—"),
                    dataset="LLMTrace",
                    accuracy=self.accuracy(neural),
                ),
            ),
            self.bind(
                ft.Text(size=13, color=MUTED),
                lambda: self.tr("model_style", accuracy=self.accuracy(style)),
            ),
            divider(),
            self.heading("limits_title"),
            *(bullet(key) for key in LIMITS),
            divider(),
            self.heading("sources_title"),
            self.label("sources_text", size=13, color=MUTED),
            self.bind(
                ft.Text(size=11, color=MUTED), lambda: self.tr("version", version=APP_VERSION)
            ),
        )
        self.info_card.visible = False  # the navigation bar shows it

    def limit_text(self, key):
        return lambda: self.tr(key, n=SHORT_WORDS)

    def build_bars(self):
        # a button per language, labelled with its code and, in the tooltip, named in its own words
        # so that it can be found whatever the current language is
        self.language_buttons = {
            code: ft.TextButton(code.upper(), tooltip=name, on_click=lambda e, c=code: self.set_language(c))
            for code, name in LANGUAGES.items()
        }
        self.top_bar = ft.AppBar(
            title=ft.Text(APP_NAME, size=18, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
            title_spacing=SCREEN_MARGIN,
            bgcolor=SURFACE,
            elevation=0,
            actions=[
                ft.Container(
                    padding=ft.Padding.only(right=SCREEN_MARGIN),
                    content=ft.Row(list(self.language_buttons.values()), spacing=6),
                )
            ],
        )
        self.nav_bar = ft.NavigationBar(
            selected_index=0,
            bgcolor=SURFACE,
            destinations=[
                self.bind(
                    ft.NavigationBarDestination(
                        icon=ft.Icons.FACT_CHECK_OUTLINED, selected_icon=ft.Icons.FACT_CHECK
                    ),
                    lambda: self.tr("nav_check"),
                    attr="label",
                ),
                self.bind(
                    ft.NavigationBarDestination(icon=ft.Icons.INFO_OUTLINED, selected_icon=ft.Icons.INFO),
                    lambda: self.tr("nav_info"),
                    attr="label",
                ),
            ],
            on_change=self.show_page,
        )

    def show_page(self, e):
        shown = e.control.selected_index
        for index, card in enumerate((self.check_card, self.info_card)):
            card.visible = index == shown
        self.page.update()
        self.page.run_task(self.page.scroll_to, offset=0)  # a page opens from its top

    # ---- the check page --------------------------------------------------
    def counter_text(self):
        words = count_words(self.field.value or "")
        return self.tr("counter_short" if 0 < words < SHORT_WORDS else "counter", n=words)

    def update_counter(self):
        words = count_words(self.field.value or "")
        self.counter.value = self.counter_text()
        self.counter.color = ft.Colors.AMBER_400 if 0 < words < SHORT_WORDS else MUTED

    def on_change(self, e):
        self.update_counter()
        self.verdict = self.message = self.style = None  # the verdict on show was for the old text
        self.render()
        self.page.update()

    def clear(self, e=None):
        self.field.value = ""
        self.on_change(None)

    async def paste(self, e=None):
        """Replace the text with what is on the clipboard (the user presses Check when it is the right text)."""
        try:
            text = await self.read_clipboard() if self.read_clipboard else None
        except Exception:  # a clipboard that cannot be read is told to the user like an empty one
            log.warning("could not read the clipboard", exc_info=True)
            text = None
        if not text or not text.strip():
            self.verdict = self.style = None
            self.message = "clipboard"
            self.render()
            self.page.update()
            return
        self.field.value = text
        self.on_change(None)

    def use_sample(self, text):
        self.field.value = text
        self.on_change(None)
        self.check()

    def set_busy(self, busy):
        self.spinner.visible = busy
        self.check_button.disabled = busy
        self.page.update()

    def warm_up(self):
        try:
            self.analyzer.warm_up()
        except Exception:  # check() reports it when the user asks for the reasons
            log.warning("could not warm up the stylometry", exc_info=True)

    def check(self, e=None):
        text = self.field.value or ""
        self.verdict = self.message = self.style = None
        if not text.strip():
            self.message = "empty"
            self.render()
            self.page.update()
            return
        self.set_busy(True)
        try:
            self.verdict = assess(self.detector, text)
        except Exception:
            log.exception("the check failed")
            self.message = "error"
        else:
            if self.analyzer is not None and self.verdict.kind != "foreign":
                self.style = "loading"
        self.render()
        self.page.update()  # the answer of the neural model first, the reasons when they are ready
        if self.style == "loading":
            try:
                self.style = self.analyzer.analyze(text)
            except Exception as error:
                log.warning("the stylometry failed", exc_info=True)
                self.style = ("error", f"{type(error).__name__}: {error}")
            self.render()
        self.set_busy(False)

    # ---- the verdict card --------------------------------------------------
    def render(self):
        """Draw the card for the state the screen is in (nothing, a message or a verdict)."""
        verdict = self.verdict
        kind = self.message if verdict is None else verdict.kind
        self.result.visible = kind is not None
        if kind is None:
            return
        icon, color = LOOKS[kind]
        self.icon.icon, self.icon.color = icon, color
        self.title.value, self.title.color = self.tr(f"verdict_{kind}"), color
        self.bar.visible = verdict is not None and verdict.p_ai is not None
        notes = []
        if verdict is None:
            self.detail.value = self.tr(f"detail_{kind}")
        elif kind == "foreign":
            self.detail.value = self.tr("detail_foreign")
        else:
            self.detail.value = self.tr("detail_probability", p=self.percent(verdict.p_ai))
            if verdict.pieces > 1:
                self.detail.value += self.tr("detail_pieces", n=verdict.pieces)
            self.bar.value, self.bar.color = verdict.p_ai, color
            notes = [
                self.tr(
                    f"note_{name}",
                    n=SHORT_WORDS,
                    read=verdict.chars - verdict.unread,
                    total=verdict.chars,
                )
                for name in verdict.notes
            ]
        self.notes.controls = [
            ft.Row(
                [
                    ft.Icon(icon=ft.Icons.WARNING_AMBER, size=18, color=ft.Colors.AMBER_400),
                    ft.Text(text, size=13, expand=True),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
            for text in notes
        ]
        self.style_box.visible = self.style is not None
        self.render_style()

    def render_style(self):
        """Draw the reasons: the answer of stylometry and what tipped it."""
        style = self.style
        if style is None:
            self.style_body.controls = []
        elif style == "loading":
            self.style_body.controls = [ft.Text(self.tr("style_loading"), size=13, color=MUTED)]
        elif isinstance(style, tuple):
            self.style_body.controls = [
                ft.Text(self.tr("style_unavailable", error=style[1]), size=13, color=MUTED)
            ]
        else:
            self.style_body.controls = self.reasons(style)

    def reasons(self, report):
        lang = self.lang
        own = decide(report.p_ai, 0.5)
        key = agreement(self.verdict.kind, own)
        muted = lambda text, **style: ft.Text(text, size=12, color=MUTED, **style)  # noqa: E731
        controls = [
            ft.Text(
                self.tr("style_probability", p=self.percent(report.p_ai)),
                size=14,
                weight=ft.FontWeight.W_600,
            ),
            ft.ProgressBar(value=report.p_ai, bar_height=8, color=LOOKS[own][1]),
            ft.Text(self.tr(key), size=13, color=AGREEMENT_COLOURS[key]),
            ft.Divider(height=8, color=SURFACE),
            ft.Text(self.tr("groups_title"), size=15, weight=ft.FontWeight.W_600),
            muted(self.tr("groups_hint")),
        ]
        peak = max((abs(effect) for effect in report.groups.values()), default=0) or 1.0
        for group, effect in report.groups.items():
            controls.append(self.group_row(self.tr(f"group_{group}"), effect, peak))
        controls += [
            ft.Divider(height=8, color=SURFACE),
            ft.Text(self.tr("reasons_title"), size=15, weight=ft.FontWeight.W_600),
        ]
        for reason in report.reasons[:TOP_REASONS]:
            toward = "toward_ai" if reason.effect > 0 else "toward_human"
            colour = LOOKS["ai" if reason.effect > 0 else "human"][1]
            controls.append(
                ft.Row(
                    [
                        ft.Text(self.tr(f"feat_{reason.feature}"), size=13, weight=ft.FontWeight.W_600, expand=True),
                        ft.Text(f"{signed(reason.effect, lang)} {self.tr(toward)}", size=12, color=colour),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                )
            )
        controls.append(muted(self.tr("style_footnote")))
        return controls

    def group_row(self, name, effect, peak):
        """A bar from the centre: to the right for "machine", to the left for "human"."""
        weight = round(100 * abs(effect) / peak)
        colour = LOOKS["ai" if effect > 0 else "human"][1]

        def half(outward_first):
            fill = ft.Container(height=BAR_HEIGHT, bgcolor=colour, border_radius=BAR_HEIGHT / 2)
            rest = ft.Container(height=BAR_HEIGHT)
            if weight == 0:
                return ft.Row([rest], spacing=0, expand=True)
            fill.expand, rest.expand = weight, 100 - weight
            parts = [fill, rest] if outward_first else [rest, fill]
            return ft.Row([part for part in parts if part.expand], spacing=0, expand=True)

        left = half(False) if effect < 0 else ft.Row([ft.Container(height=BAR_HEIGHT, expand=True)], expand=True)
        right = half(True) if effect > 0 else ft.Row([ft.Container(height=BAR_HEIGHT, expand=True)], expand=True)
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(name, size=13, expand=True),
                        ft.Text(signed(effect, self.lang), size=13, color=colour),
                    ]
                ),
                ft.Row(
                    [left, ft.Container(width=1, height=BAR_HEIGHT + 6, bgcolor=OUTLINE), right],
                    spacing=0,
                ),
            ],
            spacing=2,
        )
