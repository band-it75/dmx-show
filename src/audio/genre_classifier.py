from __future__ import annotations

from transformers import pipeline
import numpy as np


class GenreClassifier:
    """Wrapper around a pre-trained genre classification pipeline."""

    def __init__(self, model_name: str = "dima806/music_genres_classification") -> None:
        self.model_name = model_name
        self._classifier = None

    def classify(self, samples: np.ndarray, samplerate: int) -> str:
        """Return the top predicted genre label for the given audio."""
        if self._classifier is None:
            self._classifier = pipeline("audio-classification", model=self.model_name)
        result = self._classifier({"array": samples, "sampling_rate": samplerate})[0]
        return result["label"]
