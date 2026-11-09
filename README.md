# AITrace

Android app that tells whether a Russian text was written by a human or a language
model, and explains the verdict. Built with Flet; works offline and is distributed
through RuStore.

## At a glance

| | |
|:--|:--|
| **What it is** | An offline Android app that detects AI-written Russian text |
| **Languages** | Russian text; Russian and English interface |
| **What you get** | Human / AI / unsure, probability, top five reasons |
| **How it works** | A compact neural model gives the verdict; a stylometric model explains it |
| **Accuracy** | 0.942 neural, 0.883 stylometric on the LLMTrace test split |
| **Size** | 36 MB model; about 150 MB APK |
| **Privacy** | No network, no registration; the text stays on the phone |
| **Platform** | Android, `arm64-v8a`, RuStore |
| **License** | MIT; see [LICENSE](LICENSE) and [third-party notices](THIRD_PARTY_NOTICES.md) |

## How it works

The **neural model** is [`cointegrated/rubert-tiny2`](https://huggingface.co/cointegrated/rubert-tiny2),
fine-tuned on the Russian part of
[LLMTrace](https://huggingface.co/datasets/iitolstykh/LLMTrace_classification)
(a corpus of human- and AI-written texts) and exported to ONNX. It is small enough
for a phone (36 MB) and gives the main verdict.

The **stylometric model** looks at 66 measurable properties of the text: word and
sentence length, punctuation, syntax, parts of speech, vocabulary diversity,
repetitions, and readability. It uses the same features as
[ru-stylometry](https://pypi.org/project/ru-stylometry/), ported to numpy so it runs
on Android. Its accuracy is 0.883, lower than the neural model, but it is the part
that explains the verdict: the app shows which features pushed the answer towards
"human" or "machine".

The app shows the verdict, the probability, the top five reasons, and the feature
groups behind them. Short texts are checked with a warning. The answer is a
probability, not proof of authorship; see [Limitations](#limitations).

## Run and test

Requires Python 3.12.

```bash
python -m pip install -r requirements.txt
python main.py
python run_tests.py
```

`run_tests.py` needs no pytest and runs the tests in `tests/`.

## Build

```bash
python -m pip install -r requirements.txt
flet build apk --yes
```

The APK targets `arm64-v8a` and needs Flutter 3.44.8 and Java 17, the versions
used by CI. GitHub Actions runs the tests and builds the APK on every push to
`main` (`.github/workflows/build-apk.yml`) and runs the tests on every pull
request (`.github/workflows/tests.yml`). The signing key is read from the
repository secrets.

## Layout

| Path | Contents |
|:--|:--|
| `ru_detector/` | ONNX model, tokenizer, inference |
| `stylometry/` | feature extraction, numpy booster, pymorphy3 dictionaries |
| `verdict.py` | verdict rules, chunking, self-check |
| `ui.py`, `i18n.py`, `main.py` | screens and translations |
| `tests/` | test suite |
| `assets/` | app icon |
| `pyproject.toml` | Flet build settings |
| `requirements.txt` | pinned Python packages |
| `run_tests.py` | dependency-free test runner |
| `LICENSE`, `THIRD_PARTY_NOTICES.md`, `LICENSES/` | licensing and attribution |
| `.github/workflows/build-apk.yml` | CI: tests and APK build |
| `.github/workflows/tests.yml` | CI: tests on pull requests |

## Limitations

- Accuracy is measured on one corpus, LLMTrace, and eight genres; other genres and
  newer models may be harder.
- Short texts are unreliable; the app warns but still answers.
- The 0.5 threshold does not transfer to another genre: on AINL-Eval the model
  ranked texts with AUC 0.94, but at 0.5 it recognised only 35–42% of human
  annotations.

## Notes

- pymorphy3 dictionaries are shipped in `stylometry/dicts/` because Android packs
  app files into a zip and pymorphy3 cannot open them from there.
- The stylometry code is a copy of ru-stylometry 0.1.1 (MIT) with the scikit-learn
  dependency removed. Third-party licenses and attribution are in
  [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License

The project is released under the [MIT License](LICENSE). Third-party components
and data are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md); the full
license texts are in [LICENSES/](LICENSES/).
