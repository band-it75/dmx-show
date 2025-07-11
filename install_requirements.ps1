python -m pip install --upgrade pip
pip install -r requirements.txt

# Pre-load the genre classification model so the show can run offline.
python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="dima806/music_genres_classification",
    repo_type="model",
    local_dir="models/music_genres_classification",
    local_dir_use_symlinks=False,
)
PY
