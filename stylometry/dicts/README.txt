The dictionaries of pymorphy3 for Russian, copied unchanged from the package pymorphy3-dicts-ru
2.4.417150.4580142 (https://github.com/no-plagiarism/pymorphy3-dicts, MIT license according to its
metadata). They are compiled from OpenCorpora (opencorpora.org, version 0.92, revision 417150); the
terms of that data are on its site.

They live here and not in the installed package because on Android every package is packed into
one zip file, and pymorphy3 opens its dictionaries as ordinary files, which fails inside a zip
(NotADirectoryError: .../sitepackages.zip/pymorphy3_dicts_ru/data/meta.json). The app points
pymorphy3 at this folder: see stylometry/lib/_morph.py.
