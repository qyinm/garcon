from garcon.commands import (
    COMMANDS,
    SAFETY_RULES,
    execute_command,
    get_command,
    get_safety,
    register,
)
from garcon.commands.base import CommandResult


def dummy_ls(path: str = ".") -> CommandResult:
    return CommandResult(stdout="file1.txt\nfile2.txt", stderr="", success=True)


def test_register_makes_command_discoverable():
    register("ls", dummy_ls, safety={"danger": "low", "creates_files": False, "modifies_files": False})
    assert "ls" in COMMANDS
    assert get_command("ls") is dummy_ls


def test_execute_unknown_name_returns_error():
    result = execute_command("nonexistent", {})
    assert not result.success
    assert "Unknown command" in result.stderr


def test_execute_command_passes_params():
    def dummy(path: str) -> CommandResult:
        return CommandResult(stdout=path, stderr="", success=True)

    register("test_exec", dummy)
    result = execute_command("test_exec", {"path": "/tmp"})
    assert result.stdout == "/tmp"
    assert result.success


def test_command_result_stores_fields():
    result = CommandResult(
        stdout="output",
        stderr="error",
        success=False,
        undo_info={"type": "test", "items": []},
    )
    assert result.stdout == "output"
    assert result.stderr == "error"
    assert not result.success
    assert result.undo_info == {"type": "test", "items": []}


def test_command_result_defaults():
    result = CommandResult(stdout="", stderr="", success=True)
    assert result.undo_info is None


def test_get_safety_returns_default_for_unknown():
    safety = get_safety("nonexistent")
    assert safety == {"danger": "low", "creates_files": False, "modifies_files": False}


def test_get_safety_returns_registered():
    register("test_safe", dummy_ls, safety={"danger": "high", "creates_files": False, "modifies_files": True})
    safety = get_safety("test_safe")
    assert safety["danger"] == "high"
    assert safety["modifies_files"]
