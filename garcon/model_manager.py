import os
import shutil
import urllib.request
from pathlib import Path

MODEL_DIR = Path("~/.cache/garcon").expanduser()
MODEL_NAME = "HuggingFaceTB/SmolLM2-135M-Instruct"
MODEL_FILENAME = "SmolLM2-135M-Instruct.Q4_K_M.gguf"
MODEL_URL = (
    "https://huggingface.co/QuantFactory/"
    "SmolLM2-135M-Instruct-GGUF/resolve/main/"
    "SmolLM2-135M-Instruct.Q4_K_M.gguf"
)


def model_path() -> str | None:
    path = MODEL_DIR / MODEL_FILENAME
    if path.exists():
        return str(path)
    return None


def is_downloaded() -> bool:
    return model_path() is not None


def model_size() -> int | None:
    path = model_path()
    if path:
        return os.path.getsize(path)
    return None


def download_model(progress_callback=None) -> str:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    dest = MODEL_DIR / MODEL_FILENAME
    tmp = dest.with_suffix(".gguf.part")

    def reporthook(count, block_size, total):
        if progress_callback and total > 0:
            pct = min(100, int(count * block_size * 100 / total))
            progress_callback(pct)

    urllib.request.urlretrieve(MODEL_URL, str(tmp), reporthook)
    shutil.move(str(tmp), str(dest))
    return str(dest)


def remove_model() -> bool:
    path = MODEL_DIR / MODEL_FILENAME
    if path.exists():
        path.unlink()
        return True
    return False
