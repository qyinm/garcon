from pathlib import Path

import pytest

from garcon.commands.register_all import register_all
from garcon.executor import (
    execute_plan,
    execute_single_step,
    show_preview,
)

register_all()

TEST_DIR = Path("tests/test_commands")


def test_single_step_ls():
    result = execute_single_step("ls_command", {"path": str(TEST_DIR)})
    assert result["success"]
    assert result["result"] is not None


def test_single_step_unknown_command():
    result = execute_single_step("nonexistent_command", {})
    assert not result["success"]
    assert "Unknown" in result["error"]


def test_single_step_cat():
    test_file = TEST_DIR / "test_exec_cat.txt"
    test_file.write_text("hello executor")
    result = execute_single_step("cat_command", {"path": str(test_file)})
    assert result["success"]
    assert "hello executor" in result["result"].stdout
    test_file.unlink(missing_ok=True)


def test_multi_step_execution():
    test_file = TEST_DIR / "test_exec_multi.txt"
    test_file.write_text("line1\nline2\nline3\n")

    actions = [
        {"action": "wc_command", "params": {"path": str(test_file)}},
    ]

    steps = execute_plan(actions)
    assert len(steps) == 1
    assert steps[0]["success"]
    assert "3" in steps[0]["result"]

    test_file.unlink(missing_ok=True)


def test_dangerous_command_blocked():
    result = execute_single_step("rm_command", {"path": "/"})
    assert not result["success"]
    assert "차단" in result["error"]


def test_show_preview_rm():
    preview = show_preview("rm_command", {"path": "test.txt", "recursive": True})
    assert "rm" in preview
    assert "test.txt" in preview


def test_show_preview_ls():
    preview = show_preview("ls_command", {"path": ".", "options": "-la"})
    assert "ls" in preview
