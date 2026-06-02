import pytest

from garcon.model_manager import (
    MODEL_FILENAME,
    MODEL_MANIFEST,
    MODEL_NAME,
    _compute_sha256,
    checksum_status,
    download_model,
    is_downloaded,
    model_path,
    model_size,
    remove_model,
)


def test_model_name_is_huggingface_tb():
    assert "HuggingFaceTB" in MODEL_NAME
    assert "SmolLM2" in MODEL_NAME


def test_manifest_has_required_keys():
    assert "id" in MODEL_MANIFEST
    assert "repo" in MODEL_MANIFEST
    assert "filename" in MODEL_MANIFEST
    assert "sha256" in MODEL_MANIFEST
    assert "size_bytes" in MODEL_MANIFEST
    assert "backend" in MODEL_MANIFEST


def test_manifest_repo_is_quant_factory():
    assert "QuantFactory" in MODEL_MANIFEST["repo"]


@pytest.mark.slow
def test_not_downloaded_by_default():
    path = model_path()
    if path:
        remove_model()
    assert model_path() is None
    assert is_downloaded() is False


@pytest.mark.slow
def test_download_and_remove():
    if not is_downloaded():
        download_model()
    assert is_downloaded() is True
    assert model_path() is not None
    assert MODEL_FILENAME in model_path()

    size = model_size()
    assert size is not None
    assert size > 90_000_000

    assert remove_model() is True
    assert is_downloaded() is False


@pytest.mark.slow
def test_remove_when_not_downloaded():
    remove_model()
    assert remove_model() is False


def test_checksum_status_not_downloaded():
    remove_model()
    assert checksum_status() == "not_downloaded"
