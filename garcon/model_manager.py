import hashlib
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

MODEL_MANIFEST = {
    "id": "smollm2-135m-instruct-q4-k-m",
    "repo": "QuantFactory/SmolLM2-135M-Instruct-GGUF",
    "filename": MODEL_FILENAME,
    "sha256": None,
    "size_bytes": 105000000,
    "backend": "llama.cpp",
}


def _compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


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


def checksum_status() -> str:
    path = MODEL_DIR / MODEL_FILENAME
    if not path.exists():
        return "not_downloaded"
    expected = MODEL_MANIFEST["sha256"]
    if expected is None:
        return "unknown"
    actual = _compute_sha256(path)
    if actual == expected:
        return "verified"
    return "mismatch"


def download_model(progress_callback=None) -> str:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    dest = MODEL_DIR / MODEL_FILENAME
    tmp = dest.with_suffix(".gguf.part")

    def reporthook(count, block_size, total):
        if progress_callback and total > 0:
            pct = min(100, int(count * block_size * 100 / total))
            progress_callback(pct)

    try:
        urllib.request.urlretrieve(MODEL_URL, str(tmp), reporthook)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise

    shutil.move(str(tmp), str(dest))

    if MODEL_MANIFEST["sha256"] is not None:
        actual = _compute_sha256(dest)
        if actual != MODEL_MANIFEST["sha256"]:
            dest.unlink()
            raise ValueError(
                "모델 파일 checksum이 일치하지 않습니다. "
                "다시 다운로드해 주세요."
            )

    return str(dest)


def remove_model() -> bool:
    path = MODEL_DIR / MODEL_FILENAME
    if path.exists():
        path.unlink()
        return True
    return False
