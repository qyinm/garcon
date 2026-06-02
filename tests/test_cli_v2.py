from pathlib import Path
from unittest.mock import patch

from garcon.cli import _parse_nl, handle, _parse_direct

TEST_DIR = Path("tests/test_commands")


def test_parse_direct_ls():
    action, params = _parse_direct("ls", "")
    assert action == "ls_command"


def test_parse_direct_cat():
    action, params = _parse_direct("cat", "test.txt")
    assert action == "cat_command"
    assert params.get("path") == "test.txt"


def test_parse_direct_grep():
    action, params = _parse_direct("grep", "error .")
    assert action == "grep_command"
    assert params.get("pattern") == "error"


def test_parse_direct_unknown():
    assert _parse_direct("foobar", "") is None


def test_parse_nl_direct():
    r = _parse_nl("ls")
    assert r and r["action"] == "ls_command"


@patch("garcon.cli.model_path")
def test_parse_nl_model_then_direct(mock_model_path):
    mock_model_path.return_value = None
    r = _parse_nl("ls")
    assert r and r["action"] == "ls_command"


def test_handle_ls():
    assert handle(f"ls {TEST_DIR}")
