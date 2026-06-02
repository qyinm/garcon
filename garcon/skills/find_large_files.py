from pathlib import Path

from garcon.skills.base import Skill, SkillResult

DEFAULT_LIMIT = 20
DEFAULT_MIN_SIZE_MB = 100


class FindLargeFilesSkill(Skill):
    name = "find_large_files"
    risk = "low"
    dry_run_supported = True

    def preview(self, args: dict) -> SkillResult:
        path = Path(args.get("path", ".")).expanduser().resolve()
        if not path.exists():
            return SkillResult(ok=False, message=f"경로를 찾을 수 없습니다: {path}")
        return SkillResult(
            ok=True,
            message=f"{path}에서 큰 파일을 검색합니다.",
        )

    def execute(self, args: dict) -> SkillResult:
        path = Path(args.get("path", ".")).expanduser().resolve()
        min_size_mb = args.get("min_size_mb", DEFAULT_MIN_SIZE_MB)
        limit = args.get("limit", DEFAULT_LIMIT)

        if not path.exists():
            return SkillResult(ok=False, message=f"경로를 찾을 수 없습니다: {path}")

        min_bytes = min_size_mb * 1024 * 1024
        large_files: list[dict] = []

        if path.is_file():
            size = path.stat().st_size
            if size >= min_bytes:
                large_files.append({
                    "path": str(path),
                    "size_mb": round(size / 1024 / 1024, 1),
                })
        else:
            try:
                for p in path.rglob("*"):
                    rel = p.relative_to(path)
                    if any(part.startswith(".") for part in rel.parts):
                        continue
                    if p.is_file():
                        size = p.stat().st_size
                        if size >= min_bytes:
                            large_files.append({
                                "path": str(p),
                                "size_mb": round(size / 1024 / 1024, 1),
                            })
                            if len(large_files) >= limit:
                                break
            except PermissionError:
                pass

        large_files.sort(key=lambda f: f["size_mb"], reverse=True)

        return SkillResult(
            ok=True,
            message=f"{path} — {len(large_files)}개 큰 파일 ({min_size_mb}MB 이상)",
            data={"files": large_files, "path": str(path), "min_size_mb": min_size_mb},
        )
