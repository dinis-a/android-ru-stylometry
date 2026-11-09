# Third-party notices

AITrace is released under the MIT License (see [LICENSE](LICENSE)). It also
contains or is built from the third-party components and data listed below.
The full license texts are in [LICENSES/](LICENSES/).

## Components and data in this repository

| Component | Version / source | License | Copyright / attribution |
|:--|:--|:--|:--|
| rubert-tiny2 | [cointegrated/rubert-tiny2](https://huggingface.co/cointegrated/rubert-tiny2) | MIT | Authors: cointegrated; the model card does not name a separate copyright holder |
| LLMTrace classification dataset | [iitolstykh/LLMTrace_classification](https://huggingface.co/datasets/iitolstykh/LLMTrace_classification), revision `252e21e3dca713bc82bc3c1ef73bf533d7c9fc7e` | Apache-2.0 | Irina Tolstykh, Aleksandra Tsybina, Sergey Yakubson, Maksim Kuprashevich |
| pymorphy3-dicts-ru | 2.4.417150.4580142, [no-plagiarism/pymorphy3-dicts](https://github.com/no-plagiarism/pymorphy3-dicts) | MIT | Copyright (c) 2022 no-plagiarism |
| ru-stylometry | 0.1.1, [dinis-a/ru-stylometry](https://github.com/dinis-a/ru-stylometry) | MIT | Copyright (c) 2026 Dinis |
| OpenCorpora dictionary data | version 0.92, revision 417150, [opencorpora.org](https://opencorpora.org/) | See the OpenCorpora terms | OpenCorpora contributors |

`ru_detector/model.onnx` is a fine-tune of rubert-tiny2 trained on the Russian
part of LLMTrace. The fine-tuned weights are distributed under the MIT License
together with the rest of this project.

## Runtime dependencies bundled into the Android APK

| Component | Version | License | Copyright / attribution |
|:--|:--|:--|:--|
| Flet | 1.0.4 | Apache-2.0 | Copyright (c) Flet authors |
| NumPy | 2.5.4 | BSD-3-Clause | Copyright (c) 2005-2026, NumPy Developers |
| ONNX Runtime | 1.31.1 | MIT | Copyright (c) Microsoft Corporation |
| tokenizers | 0.23.3 | Apache-2.0 | Copyright (c) Hugging Face |
| pymorphy3 | 2.0.6 | MIT | Copyright (c) 2022 Danylo Halaiko (no-plagiarism) |
| pymorphy3-dicts-ru | 2.4.417150.4580142 | MIT | Copyright (c) 2022 no-plagiarism |

The build also pulls in transitive dependencies of these packages. Each keeps
its own license; the package metadata in the build environment lists the exact
versions and licenses. The direct pins are in [requirements.txt](requirements.txt).

## Test corpus

The human texts in `tests/corpus.py` include public-domain fragments of Russian
classics and the opening sentences of the Russian Wikipedia articles
[Москва](https://ru.wikipedia.org/wiki/Москва) and
[Байкал](https://ru.wikipedia.org/wiki/Байкал), available under CC BY-SA.
The machine-written examples were produced for this project.

## License texts

- [MIT License](LICENSES/MIT.txt)
- [Apache License 2.0](LICENSES/Apache-2.0.txt)
- [BSD 3-Clause License](LICENSES/BSD-3-Clause.txt)
