from typing import Callable

from garcon.commands.base import CommandResult

COMMANDS: dict[str, Callable] = {}

SAFETY_RULES: dict[str, dict] = {}


def register(name: str, fn: Callable, safety: dict | None = None):
    COMMANDS[name] = fn
    if safety:
        SAFETY_RULES[name] = safety


def get_command(name: str) -> Callable | None:
    return COMMANDS.get(name)


def execute_command(name: str, params: dict) -> CommandResult:
    fn = get_command(name)
    if fn is None:
        return CommandResult(
            stdout="",
            stderr=f"Unknown command: {name}",
            success=False,
        )
    return fn(**params)


def get_safety(name: str) -> dict:
    return SAFETY_RULES.get(name, {"danger": "low", "creates_files": False, "modifies_files": False})
