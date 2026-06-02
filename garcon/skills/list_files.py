import os
import stat
from pathlib import Path

from garcon.skills.base import Skill, SkillResult

MAX_ENTRIES = 500


class ListFilesSkill(Skill):
    name = "list_files"
    risk = "low"
    dry_run_supported = True

    def preview(self, args: dict) -> SkillResult:
        path = Path(args.get("path", ".")).expanduser().resolve()
        if not path.exists():
            return SkillResult(ok=False, message=f"경로를 찾을 수 없습니다: {path}")
        return SkillResult(ok=True, message=f"{path}의 파일 목록을 표시합니다.")

    def execute(self, args: dict) -> SkillResult:
        path = Path(args.get("path", ".")).expanduser().resolve()
        hidden = args.get("hidden", False)
        detail = args.get("detail", False)

        if not path.exists():
            return SkillResult(ok=False, message=f"경로를 찾을 수 없습니다: {path}")

        if not path.is_dir():
            return SkillResult(ok=False, message=f"디렉토리가 아닙니다: {path}")

        entries = []
        for entry in os.scandir(str(path)):
            if not hidden and entry.name.startswith("."):
                continue

            info = {"name": entry.name}

            if detail:
                st = entry.stat()
                info["size"] = st.st_size
                info["is_dir"] = entry.is_dir()
                info["is_file"] = entry.is_file()
                info["mode"] = stat.filemode(st.st_mode)
                info["modified"] = int(st.st_mtime)

            entries.append(info)

            if len(entries) >= MAX_ENTRIES:
                break

        entries.sort(key=lambda e: (not e.get("is_dir", False), e["name"]))

        return SkillResult(
            ok=True,
            message=f"{path} — {len(entries)}개 항목",
            data={"entries": entries, "path": str(path)},
        )
