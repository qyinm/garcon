from pathlib import Path

from garcon.skills.base import Skill, SkillResult


class RenameFilesSkill(Skill):
    name = "rename_files"
    risk = "medium"
    dry_run_supported = True

    def _build_plan(self, args: dict) -> list[dict]:
        source = Path(args.get("source_dir", "")).expanduser().resolve()
        pattern = args.get("pattern", "")
        replacement = args.get("replacement", "")

        if not source.exists() or not source.is_dir():
            raise ValueError(f"폴더를 찾을 수 없습니다: {source}")

        if not pattern:
            raise ValueError("변경할 패턴을 입력해주세요.")

        plan = []

        for file in source.iterdir():
            if not file.is_file():
                continue
            if pattern in file.name:
                new_name = file.name.replace(pattern, replacement)
                dst = file.parent / new_name
                if dst.exists():
                    raise FileExistsError(f"이미 존재하는 파일입니다: {dst}")
                plan.append({
                    "from": str(file),
                    "to": str(dst),
                })

        return plan

    def preview(self, args: dict) -> SkillResult:
        try:
            plan = self._build_plan(args)
        except ValueError as e:
            return SkillResult(ok=False, message=str(e))

        return SkillResult(
            ok=True,
            message=f"{len(plan)}개 파일 이름을 변경할 예정입니다.",
            data={"plan": plan},
        )

    def execute(self, args: dict) -> SkillResult:
        try:
            plan = self._build_plan(args)
        except ValueError as e:
            return SkillResult(ok=False, message=str(e))

        renamed = []
        for item in plan:
            src = Path(item["from"])
            dst = Path(item["to"])
            src.rename(dst)
            renamed.append(item)

        return SkillResult(
            ok=True,
            message=f"{len(renamed)}개 파일 이름을 변경했습니다.",
            data={"renamed": renamed},
            undo={
                "type": "move_files_back",
                "items": [{"from": x["to"], "to": x["from"]} for x in renamed],
            },
        )
