"""Tests for how the project is put together. Run with `python run_tests.py` (pytest works too)."""

import ast
import struct
import sys
import tomllib
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ui  # noqa: E402

PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
WORKFLOW = (ROOT / ".github" / "workflows" / "build-apk.yml").read_text(encoding="utf-8")
EXCLUDED = PYPROJECT["tool"]["flet"]["app"]["exclude"]
# the import name of a package -> the name it is installed under
DISTRIBUTIONS = {"flet": "flet", "numpy": "numpy", "onnxruntime": "onnxruntime", "tokenizers": "tokenizers", "pymorphy3": "pymorphy3"}


def declared():
    return {entry.split("==")[0].split(">")[0].split("<")[0].strip().lower() for entry in PYPROJECT["project"]["dependencies"]}


def app_sources():
    """The Python files that go into the APK."""
    skipped = {ROOT / name for name in EXCLUDED}
    for path in ROOT.rglob("*.py"):
        parts = path.relative_to(ROOT).parts
        if parts[0] in {name for name in EXCLUDED} or parts[0].startswith((".", "_")):
            continue
        if path in skipped or path.name == "run_tests.py":
            continue
        yield path


def test_the_version_on_the_about_page_is_the_version_of_the_project():
    assert PYPROJECT["project"]["version"] == ui.APP_VERSION


def test_every_package_the_app_imports_is_a_dependency():
    local = {path.stem for path in ROOT.glob("*.py")} | {path.name for path in ROOT.iterdir() if path.is_dir()}
    imported = set()
    for path in app_sources():
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported.add(node.module.split(".")[0])
    third_party = {name for name in imported if name not in sys.stdlib_module_names and name not in local}
    assert third_party == set(DISTRIBUTIONS), third_party ^ set(DISTRIBUTIONS)
    assert {DISTRIBUTIONS[name] for name in third_party} <= declared()
    assert "pymorphy3-dicts-ru" in declared()  # the dictionaries are read at run time


def test_the_files_the_models_are_read_from_are_packed_into_the_apk():
    needed = [
        "ru_detector/model.onnx",
        "ru_detector/tokenizer.json",
        "ru_detector/config.json",
        "stylometry/model.npz",
        "stylometry/model.json",
    ]
    for name in needed:
        assert (ROOT / name).is_file(), name
        assert not any(name == path or name.startswith(path + "/") for path in EXCLUDED), name


def first_row_of_the_icon():
    """Size and the first row of pixels (RGBA) of assets/icon.png, read without any imaging library."""
    data = (ROOT / "assets" / "icon.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG file"
    position, header, pixels = 8, b"", b""
    while position < len(data):
        length = struct.unpack(">I", data[position : position + 4])[0]
        tag, body = data[position + 4 : position + 8], data[position + 8 : position + 8 + length]
        if tag == b"IHDR":
            header = body
        elif tag == b"IDAT":
            pixels += body
        position += 12 + length
    width, height, depth, colour, _, _, interlace = struct.unpack(">IIBBBBB", header)
    assert (depth, colour, interlace) == (8, 6, 0), "the icon has to be 8-bit RGBA without interlacing"
    raw = zlib.decompressobj().decompress(pixels, 1 + 4 * width)
    row = bytearray(raw[1:])
    if raw[0] in (1, 3, 4):  # of a first row, the filters that look at the pixel to the left
        for i in range(4, len(row)):
            row[i] = (row[i] + (row[i - 4] >> 1 if raw[0] == 3 else row[i - 4])) & 255
    return width, height, row


def test_the_app_has_its_own_icon_on_a_transparent_background():
    width, height, row = first_row_of_the_icon()
    assert width == height >= 512  # Flet takes assets/icon.png and no other name
    # Flet adds the margin for Android's round mask only around a picture with a transparent background
    assert not any(row[3::4]), "the top row of the icon is not transparent"


def test_what_the_app_does_not_need_is_left_out_of_the_apk():
    for name in ("tests", "tools", "Makefile", "finetune_android.ipynb", "run_tests.py"):
        assert name in EXCLUDED, name


def test_the_ci_runs_the_tests_before_it_builds_the_apk():
    assert "python run_tests.py" in WORKFLOW and "flet build apk" in WORKFLOW
    assert WORKFLOW.index("python run_tests.py") < WORKFLOW.index("flet build apk")
    assert "upload-artifact" in WORKFLOW


def test_the_ci_uses_the_flet_that_the_project_is_built_for():
    pinned = [entry for entry in PYPROJECT["project"]["dependencies"] if entry.startswith("flet")]
    assert pinned and pinned[0].startswith("flet==")
    version = pinned[0].split("==")[1]
    assert f'FLET_VERSION: "{version}"' in WORKFLOW
