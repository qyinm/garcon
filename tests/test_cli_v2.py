from pathlib import Path
from unittest.mock import patch

from garcon.cli import _parse_nl

TEST_DIR = Path("tests/test_commands")


@patch("garcon.cli.model_path")
def test_parse_nl_no_model(mock_model_path):
    mock_model_path.return_value = None
    assert _parse_nl("ls") is None


@patch("garcon.cli.model_path")
def test_parse_nl_with_model(mock_model_path):
    mock_model_path.return_value = "/fake/model.gguf"
    with patch("garcon.model_router.router") as mock_router:
        mock_router.return_value = {"action": "ls_command", "params": {"path": str(TEST_DIR)}}
        r = _parse_nl("파일 목록 보여줘")
        assert r and r["action"] == "ls_command"
