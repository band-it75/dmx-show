from __future__ import annotations

from pathlib import Path
from transformers import pipeline
import numpy as np


class GenreClassifier:
    """Wrapper around a pre-trained genre classification pipeline."""

    def __init__(self, model_path: str | Path | None = None) -> None:
        if model_path is None:
            root_dir = Path(__file__).resolve().parents[2]
            model_path = root_dir / "models" / "music_genres_classification"
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Genre model not found at {self.model_path}")
        self._classifier = None

    def classify(self, samples: np.ndarray, samplerate: int) -> str:
        """Return the top predicted genre label for the given audio."""
        if self._classifier is None:
            self._classifier = pipeline(
                "audio-classification",
                model=str(self.model_path),
                local_files_only=True,
            )
        result = self._classifier({"array": samples, "sampling_rate": samplerate})[0]
        return result["label"]
