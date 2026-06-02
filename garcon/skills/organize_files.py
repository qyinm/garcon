import shutil
from pathlib import Path

from garcon.skills.base import Skill, SkillResult


class OrganizeFilesSkill(Skill):
    name = "organize_files"
    risk = "medium"
    dry_run_supported = True

    def _build_plan(self, args: dict) -> list[dict]:
        source = Path(args.get("source_dir", "")).expanduser().resolve()
        rules = args.get("rules", [])

        if not source.exists() or not source.is_dir():
            raise ValueError(f"폴더를 찾을 수 없습니다: {source}")

        plan = []
        seen = set()

        for rule in rules:
            extensions = {
                ext.lower().lstrip(".")
                for ext in rule.get("extensions", [])
            }
            target = Path(rule.get("target_dir", "")).expanduser()

            if not target:
                continue

            for file in source.iterdir():
                if not file.is_file():
                    continue

                ext = file.suffix.lower().lstrip(".")
                if ext in extensions:
                    dst = target / file.name
                    if dst in seen:
                        continue
                    seen.add(dst)
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
            message=f"{len(plan)}개 파일을 이동할 예정입니다.",
            data={"plan": plan},
        )

    def execute(self, args: dict) -> SkillResult:
        try:
            plan = self._build_plan(args)
        except ValueError as e:
            return SkillResult(ok=False, message=str(e))

        moved = []
        for item in plan:
            src = Path(item["from"])
            dst = Path(item["to"])

            if dst.exists():
                raise FileExistsError(f"이미 존재하는 파일입니다: {dst}")

            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            moved.append(item)

        return SkillResult(
            ok=True,
            message=f"{len(moved)}개 파일을 이동했습니다.",
            data={"moved": moved},
            undo={
                "type": "move_files_back",
                "items": [{"from": x["to"], "to": x["from"]} for x in moved],
            },
        )
