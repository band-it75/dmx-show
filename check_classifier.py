from transformers import pipeline
import numpy as np

print("✅ transformers imported")

try:
    import torch
    print("✅ torch available: version", torch.__version__)
except ImportError:
    print("❌ torch not installed")

try:
    import torchaudio
    print("✅ torchaudio available")
except ImportError:
    print("❌ torchaudio not installed")

print("Loading model pipeline...")
classifier = pipeline(
    "audio-classification",
    model="models/music_genres_classification",
    local_files_only=True,
)
print("✅ pipeline loaded")

samples = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 16000))
result = classifier({"array": samples, "sampling_rate": 16000})
print("Prediction:", result)
