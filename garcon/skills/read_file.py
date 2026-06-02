from pathlib import Path

from garcon.skills.base import Skill, SkillResult

DEFAULT_MAX_LINES = 100
MAX_FILE_SIZE = 10 * 1024 * 1024

BINARY_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp",
    ".mp3", ".mp4", ".avi", ".mov", ".mkv", ".wav", ".flac",
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".o", ".so", ".dylib", ".dll", ".exe",
    ".pyc", ".pyo",
}


class ReadFileSkill(Skill):
    name = "read_file"
    risk = "low"
    dry_run_supported = True

    def preview(self, args: dict) -> SkillResult:
        path = Path(args.get("path", "")).expanduser().resolve()
        if not path.exists():
            return SkillResult(ok=False, message=f"파일을 찾을 수 없습니다: {path}")
        if path.is_dir():
            return SkillResult(ok=False, message=f"디렉토리입니다: {path}")
        return SkillResult(ok=True, message=f"{path}의 내용을 읽습니다.")

    def execute(self, args: dict) -> SkillResult:
        path = Path(args.get("path", "")).expanduser().resolve()
        max_lines = args.get("max_lines", DEFAULT_MAX_LINES)

        if not path.exists():
            return SkillResult(ok=False, message=f"파일을 찾을 수 없습니다: {path}")

        if path.is_dir():
            return SkillResult(ok=False, message=f"디렉토리입니다: {path}")

        ext = path.suffix.lower()
        if ext in BINARY_EXTS:
            return SkillResult(ok=False, message=f"바이너리 파일입니다: {path.name}")

        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            return SkillResult(
                ok=False,
                message=f"파일이 너무 큽니다 ({file_size / 1024 / 1024:.1f}MB). 최대 10MB까지 읽을 수 있습니다.",
            )

        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return SkillResult(ok=False, message=f"파일 읽기 실패: {e}")

        lines = text.splitlines()
        total_lines = len(lines)
        truncated = False

        if max_lines and len(lines) > max_lines:
            lines = lines[:max_lines]
            truncated = True

        return SkillResult(
            ok=True,
            message=f"{path} — {total_lines}줄 중 {len(lines)}줄 표시"
            + (" (일부만 표시)" if truncated else ""),
            data={
                "lines": lines,
                "total_lines": total_lines,
                "shown_lines": len(lines),
                "path": str(path),
                "truncated": truncated,
            },
        )
