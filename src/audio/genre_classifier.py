from __future__ import annotations

from pathlib import Path
from typing import TextIO
from transformers import pipeline, is_torch_available, is_tf_available
import numpy as np


class GenreClassifier:
    """Wrapper around a pre-trained genre classification pipeline."""

    def __init__(
        self,
        model_path: str | Path | None = None,
        verbose: bool = False,
        log_file: str | Path | None = None,
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
        self.log_file: TextIO | None = None
        if log_file is not None:
            self.log_file = open(log_file, "a")

    def _log(self, message: str) -> None:
        if self.log_file:
            self.log_file.write(message + "\n")
            self.log_file.flush()
        if self.verbose:
            print(message, flush=True)

    def classify(self, samples: np.ndarray, samplerate: int) -> str:
        """Return the top predicted genre label for the given audio."""
        if self._classifier is None:
            self._log(f"Loading genre model from {self.model_path}")
            self._classifier = pipeline(
                "audio-classification",
                model=str(self.model_path),
                local_files_only=True,
            )
        self._log(
            f"classify: samples={samples.shape} samplerate={samplerate}"
        )
        result = self._classifier({"array": samples, "sampling_rate": samplerate})
        if not result:
            self._log("genre model returned no predictions")
            return ""
        label = result[0].get("label", "")
        self._log(f"Genre label returned: {label}")
        return label

    def __del__(self) -> None:
        if self.log_file:
            try:
                self.log_file.close()
            except Exception:
                pass
