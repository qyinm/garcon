from pathlib import Path

from garcon.skills.base import Skill, SkillResult

DEFAULT_MAX_RESULTS = 50
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_SCANNED_FILES = 5000

TEXT_EXTS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".rb", ".go", ".rs",
    ".java", ".kt", ".swift", ".c", ".cpp", ".h", ".hpp",
    ".md", ".txt", ".rst", ".json", ".yaml", ".yml", ".toml",
    ".cfg", ".ini", ".conf", ".env", ".sh", ".bash", ".zsh",
    ".html", ".css", ".scss", ".sass", ".sql", ".xml",
    ".log", ".csv", ".tsv",
    ".dockerfile", "dockerfile",
    ".gitignore", ".gitkeep",
}


def _is_text_file(path: Path, include_extensions: list[str] | None = None) -> bool:
    if path.name == "Dockerfile" or path.name.startswith("Dockerfile"):
        return True

    if include_extensions:
        ext = path.suffix.lower().lstrip(".")
        if ext in include_extensions:
            return True
        return False

    ext = path.suffix.lower()
    if ext in TEXT_EXTS:
        return True

    try:
        sample = path.read_bytes()[:4096]
    except Exception:
        return False

    if b"\x00" in sample:
        return False

    return True


class SearchTextSkill(Skill):
    name = "search_text"
    risk = "low"
    dry_run_supported = True

    def preview(self, args: dict) -> SkillResult:
        path = Path(args.get("path", ".")).expanduser().resolve()
        query = args.get("query", "")
        if not query:
            return SkillResult(ok=False, message="검색어가 비어 있습니다.")
        if not path.exists():
            return SkillResult(ok=False, message=f"경로를 찾을 수 없습니다: {path}")
        return SkillResult(
            ok=True, message=f"'{query}'를 {path}에서 검색합니다."
        )

    def execute(self, args: dict) -> SkillResult:
        path = Path(args.get("path", ".")).expanduser().resolve()
        query = args.get("query", "")
        include_extensions = args.get("include_extensions")
        max_results = args.get("max_results", DEFAULT_MAX_RESULTS)

        if not query:
            return SkillResult(ok=False, message="검색어가 비어 있습니다.")

        if not path.exists():
            return SkillResult(ok=False, message=f"경로를 찾을 수 없습니다: {path}")

        results: list[dict] = []

        skip_dirs = {
            ".venv", "venv", ".git", "__pycache__", "node_modules",
            ".egg-info", "dist", "build", ".ruff_cache", ".pytest_cache",
            ".mypy_cache", ".Trash",
        }

        if path.is_file():
            targets = [path]
        else:
            targets = []
            try:
                for p in path.rglob("*"):
                    rel = p.relative_to(path)
                    if any(part.startswith(".") for part in rel.parts):
                        continue
                    if p.parent.name in skip_dirs:
                        continue
                    targets.append(p)
            except Exception:
                targets = []

        scanned = 0
        for target in targets:
            if scanned >= MAX_SCANNED_FILES:
                break

            if not target.is_file():
                continue

            try:
                size = target.stat().st_size
            except OSError:
                continue

            if size > MAX_FILE_SIZE:
                continue

            if not _is_text_file(target, include_extensions):
                continue

            scanned += 1

            try:
                text = target.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            for i, line in enumerate(text.splitlines(), 1):
                if query in line:
                    results.append({
                        "file": str(target),
                        "line": i,
                        "content": line.strip(),
                    })
                    if len(results) >= max_results:
                        break

            if len(results) >= max_results:
                break

        return SkillResult(
            ok=True,
            message=f"'{query}' — {len(results)}개 결과"
            + (" (최대 출력)" if len(results) >= max_results and results else ""),
            data={
                "results": results,
                "total": len(results),
                "query": query,
                "path": str(path),
            },
        )
