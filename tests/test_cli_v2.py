from pathlib import Path

from garcon.cli import _parse_nl, handle

TEST_DIR = Path("tests/test_commands")


def test_parse_nl_ls():
    actions = _parse_nl("tests 폴더 ls 해줘")
    assert len(actions) > 0
    assert actions[0]["action"] == "ls_command"


def test_parse_nl_cat():
    actions = _parse_nl("test.txt 내용 읽어줘")
    assert len(actions) > 0
    assert actions[0]["action"] in ("cat_command", "ls_command")


def test_parse_nl_empty():
    actions = _parse_nl("")
    assert len(actions) == 0


def test_parse_nl_garbage():
    actions = _parse_nl("!@#$%^&*()_+")
    assert len(actions) == 0


def test_handle_unknown():
    result = handle("!@#$% 요청")
    assert result


def test_handle_ls():
    result = handle(f"{TEST_DIR} 폴더 목록 보여줘")
    assert result
