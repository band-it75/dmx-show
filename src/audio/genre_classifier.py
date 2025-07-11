from __future__ import annotations

from pathlib import Path
from transformers import pipeline, is_torch_available, is_tf_available
import numpy as np


class GenreClassifier:
    """Wrapper around a pre-trained genre classification pipeline."""

    def __init__(
        self, model_path: str | Path | None = None, verbose: bool = False
    ) -> None:
        if model_path is None:
            root_dir = Path(__file__).resolve().parents[2]
            model_path = root_dir / "models" / "music_genres_classification"
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Genre model not found at {self.model_path}")

        if not is_torch_available() and not is_tf_available():
            raise ImportError(
                "PyTorch or TensorFlow is required for genre classification"
            )

        self._classifier = None
        self.verbose = verbose

    def classify(self, samples: np.ndarray, samplerate: int) -> str:
        """Return the top predicted genre label for the given audio."""
        if self._classifier is None:
            if self.verbose:
                print(f"Loading genre model from {self.model_path}", flush=True)
            self._classifier = pipeline(
                "audio-classification",
                model=str(self.model_path),
                local_files_only=True,
            )
        if self.verbose:
            print(
                f"classify: samples={samples.shape} samplerate={samplerate}",
                flush=True,
            )
        result = self._classifier({"array": samples, "sampling_rate": samplerate})
        if not result:
            if self.verbose:
                print("genre model returned no predictions", flush=True)
            return ""
        label = result[0].get("label", "")
        if self.verbose:
            print(f"Genre label returned: {label}", flush=True)
        return label
