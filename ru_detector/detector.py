"""Detector of machine-generated Russian text for an Android app built with Flet.

The module needs numpy, onnxruntime and tokenizers only: these are the packages that Flet
builds for Android (torch is not among them). The files of the model lie next to the module:
model.onnx, tokenizer.json and config.json.

    from ru_detector import Detector

    detector = Detector()
    answer = detector.predict("Текст для проверки.")
    answer["label"], answer["p_ai"]
"""

import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer


class Detector:
    """Loads the model once; predict() is cheap enough to run on every press of a button."""

    def __init__(self, folder=None, threads=None):
        # Flet 0.86 and later: read the files shipped with the app relative to __file__.
        folder = Path(folder) if folder is not None else Path(__file__).resolve().parent
        self.config = json.loads((folder / "config.json").read_text(encoding="utf-8"))
        self.max_len = int(self.config["max_len"])
        self.char_limit = int(self.config["char_limit"])
        self.threshold = float(self.config["threshold"])
        self.labels = list(self.config["labels"])
        self.tokenizer = Tokenizer.from_file(str(folder / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=self.max_len)
        options = ort.SessionOptions()
        if threads:
            options.intra_op_num_threads = int(threads)
        self.session = ort.InferenceSession(
            str(folder / "model.onnx"), options, providers=["CPUExecutionProvider"]
        )

    def predict(self, text):
        """Verdict for one text: label, probability of the machine class, tokens, truncation.

        Only the beginning of a long text is read (max_len tokens), as in training.
        """
        if not isinstance(text, str) or not text.strip():
            raise ValueError("the text is empty")
        encoded = self.tokenizer.encode(text[: self.char_limit])
        ids = np.asarray([encoded.ids], dtype=np.int64)
        feed = {"input_ids": ids, "attention_mask": np.ones_like(ids)}
        logits = self.session.run(None, feed)[0][0].astype(np.float64)
        weights = np.exp(logits - logits.max())
        p_ai = float(weights[1] / weights.sum())
        return {
            "label": self.labels[int(p_ai >= self.threshold)],
            "p_ai": p_ai,
            "tokens": int(ids.shape[1]),
            "truncated": len(text) > self.char_limit or len(encoded.overflowing) > 0,
        }


if __name__ == "__main__":
    import sys

    detector = Detector()
    for sample in sys.argv[1:] or ["Мама мыла раму."]:
        print(detector.predict(sample))
