"""UI texts in every supported language, the choice of the language and language-aware numbers.

Pure Python with no UI imports, so it can be tested without Flet installed.
"""

from collections.abc import Iterable

# language code -> the language's name in that language (the tooltip of its button in the top bar)
LANGUAGES = {"ru": "Русский", "en": "English"}
# the app reads Russian texts, so a phone set to another language still gets the Russian screen
DEFAULT_LANGUAGE = "ru"

# language code -> {text key: text}. Every language needs exactly the same keys and the same
# {placeholders} in each text (the tests check both). feat_<name> labels the features of the
# stylometric model (stylometry/model.json), group_<name> their groups.
TEXTS: dict[str, dict[str, str]] = {
    "ru": {
        "decimal_separator": ",",
        "window_title": "Проверка текста",
        "nav_check": "Проверка",
        "nav_info": "О приложении",
        # check page
        "title": "Проверка текста",
        "subtitle": "Написан ли русский текст человеком или нейросетью?",
        "field_label": "Текст",
        "field_hint": "Вставьте текст на русском языке",
        "counter": "Слов: {n}",
        "counter_short": "Слов: {n}. Короткий текст: модель на нём ошибается чаще.",
        "button_check": "Проверить",
        "button_clear": "Очистить",
        "examples": "Примеры:",
        "example_machine": "нейросеть",
        "example_human": "классика",
        # the verdict
        "verdict_ai": "Скорее всего, написано нейросетью",
        "verdict_human": "Скорее всего, написано человеком",
        "verdict_unsure": "Не удаётся определить",
        "verdict_foreign": "Не похоже на русский текст",
        "verdict_empty": "Введите текст",
        "verdict_error": "Не удалось проверить текст",
        "detail_probability": "Вероятность машинного текста по оценке нейросетевой модели: {p}",
        "detail_pieces": " (по {n} фрагментам текста)",
        "detail_empty": "Вставьте или напишите текст, который нужно проверить.",
        "detail_foreign": "Модель обучена на русских текстах, для других языков её ответ ничего не значит.",
        "detail_error": "Попробуйте ещё раз или перезапустите приложение.",
        "percent_less": "меньше 1%",
        "percent_more": "больше 99%",
        "note_short": (
            "Текст короткий, а на коротких текстах модель работает плохо и часто ошибается. "
            "Надёжнее всего она работает на абзацах — от {n} слов."
        ),
        "note_unformatted": (
            "В тексте нет заглавных букв или знаков препинания. Модель сильно реагирует на "
            "оформление: без него она склонна считать любой текст человеческим."
        ),
        "note_partial": "Текст длинный, прочитано только начало: {read} из {total} символов.",
        "banner_broken": (
            "Модель на этом устройстве работает неправильно, ответам верить нельзя. Причина: {problem}"
        ),
        "banner_load": "Не удалось загрузить модель: {error}",
        # the reasons (stylometry)
        "style_title": "Почему такой ответ: стилометрия",
        "style_intro": (
            "Нейросеть не объясняет своих решений. Поэтому текст разбирается ещё и по 66 признакам "
            "стиля (длина предложений, части речи, знаки препинания и другие). Эта модель проще и "
            "слабее, но показывает, что именно склонило её ответ."
        ),
        "style_loading": "Анализ стиля…",
        "style_unavailable": "Стилометрический разбор недоступен: {error}",
        "style_probability": "Стилометрия: вероятность машинного текста {p}",
        "agree_yes": "Обе модели дают один и тот же ответ.",
        "agree_no": "Модели расходятся: ответу стоит верить меньше.",
        "agree_partial": "Одна из моделей не уверена в ответе.",
        "groups_title": "Какие виды признаков повлияли",
        "groups_hint": "Вправо — к «нейросеть», влево — к «человек».",
        "reasons_title": "Главные причины",
        "reason_values": "В тексте: {value} · у людей: {human} · у нейросетей: {machine}",
        "toward_ai": "→ нейросеть",
        "toward_human": "→ человек",
        "style_footnote": (
            "Влияние — насколько изменился бы ответ стилометрии (в логарифме шансов), если заменить "
            "признак типичным значением по обучающим текстам. Влияния не складываются: связанные "
            "признаки делят вклад, поэтому виды признаков оценены отдельно."
        ),
        "group_char": "Символы",
        "group_typography": "Типографика",
        "group_lexical": "Словарь",
        "group_syntax": "Синтаксис",
        "group_readability": "Читаемость",
        "group_repetition": "Повторы",
        "group_morph": "Морфология",
        "feat_letter_ratio": "Доля букв среди символов",
        "feat_digit_ratio": "Доля цифр среди символов",
        "feat_punct_ratio": "Доля знаков препинания среди символов",
        "feat_symbol_ratio": "Доля символов и эмодзи среди символов",
        "feat_upper_ratio": "Доля заглавных среди букв",
        "feat_latin_ratio": "Доля латиницы среди букв",
        "feat_yo_ratio": "Доля «ё» среди «е» и «ё»",
        "feat_comma_per100w": "Запятых на 100 слов",
        "feat_colon_per100w": "Двоеточий на 100 слов",
        "feat_semicolon_per100w": "Точек с запятой на 100 слов",
        "feat_dash_per100w": "Тире на 100 слов",
        "feat_em_dash_share": "Доля длинных тире (—) среди тире",
        "feat_quote_per100w": "Кавычек на 100 слов",
        "feat_guillemet_share": "Доля «ёлочек» среди кавычек",
        "feat_paren_per100w": "Скобок на 100 слов",
        "feat_question_per100w": "Вопросительных знаков на 100 слов",
        "feat_exclam_per100w": "Восклицательных знаков на 100 слов",
        "feat_ellipsis_per100w": "Многоточий на 100 слов",
        "feat_avg_word_len": "Средняя длина слова (букв)",
        "feat_std_word_len": "Разброс длины слов",
        "feat_long_word_ratio": "Доля длинных слов (больше 6 букв)",
        "feat_mattr_50": "Разнообразие слов (MATTR-50)",
        "feat_mtld": "Лексическое разнообразие (MTLD)",
        "feat_yule_k": "Повторяемость словаря (K Юла)",
        "feat_hapax_ratio": "Доля слов, встреченных один раз",
        "feat_avg_sentence_len": "Средняя длина предложения (слов)",
        "feat_std_sentence_len": "Разброс длины предложений",
        "feat_short_sentence_ratio": "Доля коротких предложений (до 5 слов)",
        "feat_long_sentence_ratio": "Доля длинных предложений (от 25 слов)",
        "feat_function_word_ratio": "Доля служебных слов",
        "feat_negation_ratio": "Доля отрицаний",
        "feat_conj_start_ratio": "Доля предложений, начинающихся с союза",
        "feat_opener_diversity": "Разнообразие первых слов предложений",
        "feat_discourse_marker_per100w": "Вводных связок («таким образом») на 100 слов",
        "feat_avg_syllables_per_word": "Средняя длина слова (слогов)",
        "feat_polysyllabic_ratio": "Доля длинных слов (от 4 слогов)",
        "feat_lix": "Индекс сложности LIX",
        "feat_zlib_ratio": "Размер после сжатия (меньше — больше повторов)",
        "feat_repeated_bigram_ratio": "Доля повторяющихся пар слов",
        "feat_repeated_trigram_ratio": "Доля повторяющихся троек слов",
        "feat_noun_ratio": "Доля существительных",
        "feat_verb_ratio": "Доля глаголов",
        "feat_infinitive_ratio": "Доля инфинитивов",
        "feat_adj_ratio": "Доля прилагательных",
        "feat_adv_ratio": "Доля наречий",
        "feat_pronoun_ratio": "Доля местоимений-существительных",
        "feat_prep_ratio": "Доля предлогов",
        "feat_conj_ratio": "Доля союзов",
        "feat_particle_ratio": "Доля частиц",
        "feat_participle_ratio": "Доля причастий",
        "feat_gerund_ratio": "Доля деепричастий",
        "feat_autosemantic_ratio": "Доля знаменательных слов",
        "feat_analytic_ratio": "Доля предлогов, союзов и частиц",
        "feat_case_nomn_share": "Доля именительного падежа",
        "feat_case_gent_share": "Доля родительного падежа",
        "feat_case_datv_share": "Доля дательного падежа",
        "feat_case_accs_share": "Доля винительного падежа",
        "feat_case_ablt_share": "Доля творительного падежа",
        "feat_case_loct_share": "Доля предложного падежа",
        "feat_verb_past_share": "Доля глаголов прошедшего времени",
        "feat_verb_pres_share": "Доля глаголов настоящего времени",
        "feat_first_person_ratio": "Доля форм первого лица",
        "feat_second_person_ratio": "Доля форм второго лица",
        "feat_unknown_word_ratio": "Доля слов, незнакомых словарю",
        "feat_lemma_mattr_50": "Разнообразие лемм (MATTR-50)",
        "feat_wordforms_per_lemma": "Словоформ на одну лемму",
        # about page
        "about_title": "О приложении",
        "about_text": (
            "Приложение определяет, написан ли русский текст человеком или нейросетью, и "
            "объясняет, почему ответ именно такой."
        ),
        "how_title": "Как пользоваться",
        "how_step_1": "Вставьте текст на русском языке или нажмите на пример.",
        "how_step_2": (
            "Нажмите «Проверить». Лучше всего модель работает на абзацах, на коротких текстах "
            "она ошибается чаще."
        ),
        "how_step_3": "Прочитайте ответ нейросетевой модели и вероятность машинного текста.",
        "how_step_4": (
            "Ниже смотрите, почему так: стилометрия показывает признаки стиля, которые склонили "
            "ответ в ту или другую сторону."
        ),
        "models_title": "Две модели",
        "model_neural": (
            "Нейросетевая модель ({base}, дообучена на датасете {dataset}): точность на тестовой "
            "выборке {accuracy}. Даёт основной ответ, но объяснить его не может."
        ),
        "model_style": (
            "Стилометрическая модель (пакет ru-stylometry, 66 признаков стиля, градиентный бустинг): "
            "точность на той же выборке {accuracy}. Слабее, но показывает, какие признаки повлияли."
        ),
        "limits_title": "Ограничения",
        "limit_1": "Тексты короче {n} слов модель оценивает плохо.",
        "limit_2": (
            "Нейросеть сильно реагирует на оформление: без заглавных букв и знаков препинания "
            "текст кажется ей человеческим."
        ),
        "limit_3": (
            "Точность измерена на датасете LLMTrace. На других жанрах и у новых языковых моделей "
            "она может быть ниже, особенно на формальных текстах людей."
        ),
        "limit_4": "Ответ — это вероятность, а не доказательство авторства.",
        "sources_title": "На чём построено",
        "sources_text": (
            "Датасет LLMTrace; модель rubert-tiny2 (cointegrated); пакет ru-stylometry; "
            "pymorphy3; ONNX Runtime; Flet."
        ),
        "version": "Версия {version}",
    },
    "en": {
        "decimal_separator": ".",
        "window_title": "Text check",
        "nav_check": "Check",
        "nav_info": "About",
        # check page
        "title": "Text check",
        "subtitle": "Was a Russian text written by a human or by a neural network?",
        "field_label": "Text",
        "field_hint": "Paste a text in Russian",
        "counter": "Words: {n}",
        "counter_short": "Words: {n}. Short text: the model makes more mistakes on it.",
        "button_check": "Check",
        "button_clear": "Clear",
        "examples": "Examples:",
        "example_machine": "neural network",
        "example_human": "classic",
        # the verdict
        "verdict_ai": "Most likely written by a neural network",
        "verdict_human": "Most likely written by a human",
        "verdict_unsure": "Cannot tell",
        "verdict_foreign": "Does not look like Russian text",
        "verdict_empty": "Enter a text",
        "verdict_error": "Could not check the text",
        "detail_probability": "Probability of machine text according to the neural model: {p}",
        "detail_pieces": " (from {n} parts of the text)",
        "detail_empty": "Paste or type the text to check.",
        "detail_foreign": "The model was trained on Russian texts; for other languages its answer means nothing.",
        "detail_error": "Try again or restart the app.",
        "percent_less": "less than 1%",
        "percent_more": "more than 99%",
        "note_short": (
            "The text is short, and on short texts the model works poorly and often errs. "
            "It works best on paragraphs of {n} words or more."
        ),
        "note_unformatted": (
            "The text has no capital letters or sentence marks. The model reacts strongly to "
            "formatting: without it, it tends to take any text for a human's."
        ),
        "note_partial": "The text is long, only the beginning was read: {read} of {total} characters.",
        "banner_broken": (
            "The model works incorrectly on this device; do not trust its answers. Reason: {problem}"
        ),
        "banner_load": "Could not load the model: {error}",
        # the reasons (stylometry)
        "style_title": "Why this answer: stylometry",
        "style_intro": (
            "A neural network does not explain its decisions. So the text is also analysed by 66 "
            "style features (sentence length, parts of speech, punctuation and more). That model is "
            "simpler and weaker, but it shows what exactly tipped its answer."
        ),
        "style_loading": "Analysing style…",
        "style_unavailable": "Stylometric analysis is not available: {error}",
        "style_probability": "Stylometry: probability of machine text {p}",
        "agree_yes": "Both models give the same answer.",
        "agree_no": "The models disagree: trust the answer less.",
        "agree_partial": "One of the models is unsure.",
        "groups_title": "Which kinds of features mattered",
        "groups_hint": "Right: towards “neural network”, left: towards “human”.",
        "reasons_title": "Main reasons",
        "reason_values": "In the text: {value} · humans: {human} · neural networks: {machine}",
        "toward_ai": "→ neural network",
        "toward_human": "→ human",
        "style_footnote": (
            "The effect is how much the answer of stylometry (in log-odds) would change if the "
            "feature took its typical value over the training texts. Effects do not add up: related "
            "features share the credit, so the kinds of features are measured apart."
        ),
        "group_char": "Characters",
        "group_typography": "Typography",
        "group_lexical": "Vocabulary",
        "group_syntax": "Syntax",
        "group_readability": "Readability",
        "group_repetition": "Repetition",
        "group_morph": "Morphology",
        "feat_letter_ratio": "Share of letters among characters",
        "feat_digit_ratio": "Share of digits among characters",
        "feat_punct_ratio": "Share of punctuation among characters",
        "feat_symbol_ratio": "Share of symbols and emoji among characters",
        "feat_upper_ratio": "Share of capitals among letters",
        "feat_latin_ratio": "Share of Latin among letters",
        "feat_yo_ratio": "Share of “ё” among “е” and “ё”",
        "feat_comma_per100w": "Commas per 100 words",
        "feat_colon_per100w": "Colons per 100 words",
        "feat_semicolon_per100w": "Semicolons per 100 words",
        "feat_dash_per100w": "Dashes per 100 words",
        "feat_em_dash_share": "Share of em dashes (—) among dashes",
        "feat_quote_per100w": "Quotation marks per 100 words",
        "feat_guillemet_share": "Share of «guillemets» among quotation marks",
        "feat_paren_per100w": "Parentheses per 100 words",
        "feat_question_per100w": "Question marks per 100 words",
        "feat_exclam_per100w": "Exclamation marks per 100 words",
        "feat_ellipsis_per100w": "Ellipses per 100 words",
        "feat_avg_word_len": "Mean word length (letters)",
        "feat_std_word_len": "Spread of word length",
        "feat_long_word_ratio": "Share of long words (over 6 letters)",
        "feat_mattr_50": "Word variety (MATTR-50)",
        "feat_mtld": "Lexical diversity (MTLD)",
        "feat_yule_k": "Vocabulary repetitiveness (Yule's K)",
        "feat_hapax_ratio": "Share of words seen once",
        "feat_avg_sentence_len": "Mean sentence length (words)",
        "feat_std_sentence_len": "Spread of sentence length",
        "feat_short_sentence_ratio": "Share of short sentences (up to 5 words)",
        "feat_long_sentence_ratio": "Share of long sentences (25 words or more)",
        "feat_function_word_ratio": "Share of function words",
        "feat_negation_ratio": "Share of negations",
        "feat_conj_start_ratio": "Share of sentences opening with a conjunction",
        "feat_opener_diversity": "Variety of the first words of sentences",
        "feat_discourse_marker_per100w": "Stock connectives (“таким образом”) per 100 words",
        "feat_avg_syllables_per_word": "Mean word length (syllables)",
        "feat_polysyllabic_ratio": "Share of long words (4 syllables or more)",
        "feat_lix": "LIX readability index",
        "feat_zlib_ratio": "Size after compression (lower: more repetition)",
        "feat_repeated_bigram_ratio": "Share of repeated word pairs",
        "feat_repeated_trigram_ratio": "Share of repeated word triples",
        "feat_noun_ratio": "Share of nouns",
        "feat_verb_ratio": "Share of verbs",
        "feat_infinitive_ratio": "Share of infinitives",
        "feat_adj_ratio": "Share of adjectives",
        "feat_adv_ratio": "Share of adverbs",
        "feat_pronoun_ratio": "Share of noun pronouns",
        "feat_prep_ratio": "Share of prepositions",
        "feat_conj_ratio": "Share of conjunctions",
        "feat_particle_ratio": "Share of particles",
        "feat_participle_ratio": "Share of participles",
        "feat_gerund_ratio": "Share of adverbial participles",
        "feat_autosemantic_ratio": "Share of content words",
        "feat_analytic_ratio": "Share of prepositions, conjunctions and particles",
        "feat_case_nomn_share": "Share of the nominative case",
        "feat_case_gent_share": "Share of the genitive case",
        "feat_case_datv_share": "Share of the dative case",
        "feat_case_accs_share": "Share of the accusative case",
        "feat_case_ablt_share": "Share of the instrumental case",
        "feat_case_loct_share": "Share of the prepositional case",
        "feat_verb_past_share": "Share of past-tense verbs",
        "feat_verb_pres_share": "Share of present-tense verbs",
        "feat_first_person_ratio": "Share of first-person forms",
        "feat_second_person_ratio": "Share of second-person forms",
        "feat_unknown_word_ratio": "Share of words unknown to the dictionary",
        "feat_lemma_mattr_50": "Lemma variety (MATTR-50)",
        "feat_wordforms_per_lemma": "Word forms per lemma",
        # about page
        "about_title": "About",
        "about_text": (
            "The app tells whether a Russian text was written by a human or by a neural network, "
            "and explains why the answer is what it is."
        ),
        "how_title": "How to use it",
        "how_step_1": "Paste a text in Russian or tap an example.",
        "how_step_2": (
            "Press “Check”. The model works best on paragraphs and makes more mistakes on short "
            "texts."
        ),
        "how_step_3": "Read the answer of the neural model and the probability of machine text.",
        "how_step_4": (
            "Below, see why: stylometry shows the style features that tipped the answer one way "
            "or the other."
        ),
        "models_title": "Two models",
        "model_neural": (
            "Neural model ({base}, fine-tuned on the {dataset} dataset): accuracy on the test split "
            "{accuracy}. Gives the main answer but cannot explain it."
        ),
        "model_style": (
            "Stylometric model (the ru-stylometry package, 66 style features, gradient boosting): "
            "accuracy on the same split {accuracy}. Weaker, but it shows which features mattered."
        ),
        "limits_title": "Limitations",
        "limit_1": "Texts shorter than {n} words are judged poorly.",
        "limit_2": (
            "The neural model reacts strongly to formatting: without capital letters and sentence "
            "marks a text looks human to it."
        ),
        "limit_3": (
            "Accuracy was measured on the LLMTrace dataset. On other genres and with new language "
            "models it may be lower, especially on formal human texts."
        ),
        "limit_4": "The answer is a probability, not proof of authorship.",
        "sources_title": "Built on",
        "sources_text": (
            "The LLMTrace dataset; the rubert-tiny2 model (cointegrated); the ru-stylometry "
            "package; pymorphy3; ONNX Runtime; Flet."
        ),
        "version": "Version {version}",
    },
}

# keys of the numbered steps and the limitations on the About page, in order
HOW_STEPS = tuple(key for key in TEXTS[DEFAULT_LANGUAGE] if key.startswith("how_step_"))
LIMITS = tuple(key for key in TEXTS[DEFAULT_LANGUAGE] if key.startswith("limit_"))


def pick_language(codes: Iterable[str]) -> str:
    """First of the preferred language `codes` (most wanted first) that has texts here, else Russian.

    'ru', 'RU' and 'ru_RU' / 'ru-RU' all mean Russian.
    """
    for code in codes:
        language = code.replace("-", "_").split("_")[0].lower()
        if language in LANGUAGES:
            return language
    return DEFAULT_LANGUAGE


def format_number(value: float, lang: str, digits: int) -> str:
    """1234.5 -> '1234.50' in English, '1234,50' in Russian."""
    return f"{value:.{digits}f}".replace(".", TEXTS[lang]["decimal_separator"])


def format_percent(p: float, lang: str) -> str:
    """A probability for the screen; the model is never as sure as "0%" or "100%" would say."""
    if p < 0.01:
        return TEXTS[lang]["percent_less"]
    if p > 0.99:
        return TEXTS[lang]["percent_more"]
    return f"{p:.0%}"


def format_feature(name: str, value: float, lang: str) -> str:
    """A feature value the way a reader wants it: shares as percent, the rest as numbers."""
    if name.endswith(("_ratio", "_share")):
        return format_number(100 * value, lang, 1) + "%"
    return format_number(value, lang, 1 if abs(value) >= 10 else 2)
