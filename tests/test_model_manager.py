from garcon.model_manager import (
    MODEL_FILENAME,
    MODEL_NAME,
    download_model,
    is_downloaded,
    model_path,
    model_size,
    remove_model,
)


def test_model_not_downloaded_by_default():
    path = model_path()
    if path:
        remove_model()
    assert model_path() is None
    assert is_downloaded() is False


def test_is_downloaded_after_download():
    if not is_downloaded():
        download_model()
    assert is_downloaded() is True
    assert model_path() is not None
    assert MODEL_FILENAME in model_path()


def test_model_size():
    if not is_downloaded():
        download_model()
    size = model_size()
    assert size is not None
    assert size > 90_000_000


def test_remove_model():
    if not is_downloaded():
        download_model()
    assert remove_model() is True
    assert is_downloaded() is False


def test_remove_when_not_downloaded():
    remove_model()
    assert remove_model() is False


def test_model_path_is_readable():
    if not is_downloaded():
        download_model()
    path = model_path()
    assert path is not None
    data = open(path, "rb").read()[:4]
    assert data != b""


def test_model_name_is_huggingface_tb():
    assert "HuggingFaceTB" in MODEL_NAME
    assert "SmolLM2" in MODEL_NAME
