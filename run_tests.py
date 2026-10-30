"""Dependency-free test runner: `python run_tests.py` (pytest works too)."""

import importlib.util
import inspect
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    passed = failed = 0
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        module = load(path)
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("test_") or func.__module__ != module.__name__:
                continue
            try:
                func()
            except Exception:
                failed += 1
                print(f"FAIL: {path.stem}.{name}")
                traceback.print_exc()
            else:
                passed += 1
                print(f"PASS: {path.stem}.{name}")
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
