from pathlib import Path
from unittest.mock import patch

from garcon.cli import _parse_nl, handle

TEST_DIR = Path("tests/test_commands")


@patch("garcon.cli.model_path")
def test_parse_nl_ls(mock_model_path):
    mock_model_path.return_value = "/fake/model.gguf"
    with patch("garcon.cli.model_router") as mock_router:
        mock_router.return_value = {
            "action": "ls_command",
            "params": {"path": "."},
        }
        result = _parse_nl("파일 목록 보여줘")
        assert result is not None
        assert result["action"] == "ls_command"


@patch("garcon.cli.model_path")
def test_parse_nl_finish(mock_model_path):
    mock_model_path.return_value = "/fake/model.gguf"
    with patch("garcon.cli.model_router") as mock_router:
        mock_router.return_value = {
            "action": "Finish",
            "params": {"final_answer": "안녕하세요!"},
        }
        result = _parse_nl("안녕")
        assert result is not None
        assert result["action"] == "Finish"


@patch("garcon.cli.model_path")
def test_parse_nl_no_model(mock_model_path):
    mock_model_path.return_value = None
    result = _parse_nl("파일 목록 보여줘")
    assert result is None


@patch("garcon.cli.model_path")
def test_handle_ls(mock_model_path):
    mock_model_path.return_value = "/fake/model.gguf"
    with patch("garcon.cli.model_router") as mock_router:
        mock_router.return_value = {
            "action": "ls_command",
            "params": {"path": str(TEST_DIR)},
        }
        result = handle(f"{TEST_DIR} 폴더 목록 보여줘")
        assert result
