from __future__ import annotations

import csv
import os
from time import perf_counter

import numpy as np

from .config import YAMNET_CACHE_DIR, YAMNET_URL


class ModelUnavailableError(RuntimeError):
    pass


class YamnetClassifier:
    def __init__(self):
        self._model = None
        self._class_names: list[str] | None = None
        self._load_error: str | None = None

    @property
    def ready(self) -> bool:
        return self._model is not None

    @property
    def load_error(self) -> str | None:
        return self._load_error

    def load(self) -> None:
        if self._model is not None:
            return
        try:
            YAMNET_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            os.environ.setdefault("TFHUB_CACHE_DIR", str(YAMNET_CACHE_DIR))
            import tensorflow_hub as hub

            self._model = hub.load(YAMNET_URL)
            class_map_path = self._model.class_map_path().numpy().decode("utf-8")
            with open(class_map_path, newline="", encoding="utf-8") as handle:
                self._class_names = [row["display_name"] for row in csv.DictReader(handle)]
            self._load_error = None
        except Exception as exc:
            self._model = None
            self._class_names = None
            self._load_error = str(exc)
            raise ModelUnavailableError("The YAMNet model is temporarily unavailable.") from exc

    def classify(self, waveform: np.ndarray) -> tuple[np.ndarray, list[str], int]:
        if self._model is None:
            self.load()
        assert self._model is not None and self._class_names is not None
        started = perf_counter()
        scores, _, _ = self._model(waveform)
        elapsed_ms = int((perf_counter() - started) * 1000)
        return scores.numpy(), self._class_names, elapsed_ms
