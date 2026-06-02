from typing import Any


class SkillResult:
    def __init__(
        self,
        ok: bool,
        message: str,
        data: dict[str, Any] | None = None,
        undo: dict[str, Any] | None = None,
    ):
        self.ok = ok
        self.message = message
        self.data = data
        self.undo = undo


class Skill:
    name: str = ""
    risk: str = "low"
    dry_run_supported: bool = True

    def preview(self, args: dict[str, Any]) -> SkillResult:
        raise NotImplementedError

    def execute(self, args: dict[str, Any]) -> SkillResult:
        raise NotImplementedError
