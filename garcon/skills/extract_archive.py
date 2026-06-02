import tarfile
import zipfile
from pathlib import Path

from garcon.skills.base import Skill, SkillResult

MAX_EXTRACT_SIZE = 500 * 1024 * 1024


class ExtractArchiveSkill(Skill):
    name = "extract_archive"
    risk = "medium"
    dry_run_supported = True

    def preview(self, args: dict) -> SkillResult:
        archive = Path(args.get("archive", "")).expanduser().resolve()
        target_dir = Path(args.get("target_dir", ".")).expanduser().resolve()

        if not archive.exists():
            return SkillResult(ok=False, message=f"파일을 찾을 수 없습니다: {archive}")

        return SkillResult(
            ok=True,
            message=f"{archive.name}을 {target_dir}에 압축 해제합니다.",
            data={"plan": [{"file": str(archive)}], "target_dir": str(target_dir)},
        )

    def execute(self, args: dict) -> SkillResult:
        archive = Path(args.get("archive", "")).expanduser().resolve()
        target_dir = Path(args.get("target_dir", ".")).expanduser().resolve()

        if not archive.exists():
            return SkillResult(ok=False, message=f"파일을 찾을 수 없습니다: {archive}")

        suffix = archive.suffix.lower()
        if suffix not in (".zip", ".tar", ".gz", ".bz2", ".xz"):
            return SkillResult(
                ok=False,
                message=f"지원하지 않는 포맷입니다: {suffix}",
            )

        target_dir.mkdir(parents=True, exist_ok=True)

        extracted = []

        if suffix == ".zip":
            with zipfile.ZipFile(str(archive), "r") as zf:
                total_size = sum(
                    info.file_size for info in zf.infolist()
                )
                if total_size > MAX_EXTRACT_SIZE:
                    return SkillResult(
                        ok=False,
                        message=(
                            "압축 파일이 너무 큽니다."
                            " 최대 500MB까지 해제 가능합니다."
                        ),
                    )
                zf.extractall(str(target_dir))
                extracted = [
                    str(target_dir / name)
                    for name in zf.namelist()
                ]
        else:
            mode = "r:" if suffix == ".tar" else f"r:{suffix.lstrip('.')}"
            with tarfile.open(str(archive), mode) as tf:
                members = tf.getmembers()
                total_size = sum(m.size for m in members if m.isfile())
                if total_size > MAX_EXTRACT_SIZE:
                    return SkillResult(
                        ok=False,
                        message=(
                            "압축 파일이 너무 큽니다."
                            " 최대 500MB까지 해제 가능합니다."
                        ),
                    )
                tf.extractall(str(target_dir))
                extracted = [
                    str(target_dir / m.name) for m in members
                ]

        return SkillResult(
            ok=True,
            message=(
                f"{archive.name}을 {target_dir}에 해제했습니다"
                f" ({len(extracted)}개 항목)."
            ),
            data={"extracted": extracted, "target_dir": str(target_dir)},
            undo={
                "type": "delete_files",
                "items": [{"path": p} for p in extracted],
            },
        )
