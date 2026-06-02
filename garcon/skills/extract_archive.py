import tarfile
import zipfile
from pathlib import Path

from garcon.skills.base import Skill, SkillResult

MAX_EXTRACT_SIZE = 500 * 1024 * 1024


def safe_join(base: Path, member_name: str) -> Path:
    dest = (base / member_name).resolve()
    base_resolved = base.resolve()
    if dest != base_resolved and not dest.is_relative_to(base_resolved):
        raise ValueError(f"안전하지 않은 압축 경로입니다: {member_name}")
    return dest


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

        try:
            extracted = self._do_extract(archive, target_dir, suffix)
        except ValueError as e:
            return SkillResult(ok=False, message=str(e))

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

    def _do_extract(self, archive: Path, target_dir: Path, suffix: str) -> list[str]:
        extracted: list[str] = []

        if suffix == ".zip":
            with zipfile.ZipFile(str(archive), "r") as zf:
                total_size = sum(info.file_size for info in zf.infolist())
                if total_size > MAX_EXTRACT_SIZE:
                    raise ValueError("압축 파일이 너무 큽니다. 최대 500MB까지 해제 가능합니다.")

                for info in zf.infolist():
                    member_path = safe_join(target_dir, info.filename)
                    if info.is_dir():
                        member_path.mkdir(parents=True, exist_ok=True)
                        extracted.append(str(member_path))
                        continue

                    if member_path.exists():
                        continue

                    member_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(info) as src, open(member_path, "wb") as dst:
                        dst.write(src.read())
                    extracted.append(str(member_path))
        else:
            mode = "r:" if suffix == ".tar" else f"r:{suffix.lstrip('.')}"
            with tarfile.open(str(archive), mode) as tf:
                members = tf.getmembers()
                total_size = sum(m.size for m in members if m.isfile())
                if total_size > MAX_EXTRACT_SIZE:
                    raise ValueError("압축 파일이 너무 큽니다. 최대 500MB까지 해제 가능합니다.")

                for member in members:
                    if member.issym() or member.islnk():
                        raise ValueError(
                            f"심볼릭 링크/하드링크는 해제할 수 없습니다: {member.name}"
                        )

                    member_path = safe_join(target_dir, member.name)
                    if member.isdir():
                        member_path.mkdir(parents=True, exist_ok=True)
                        extracted.append(str(member_path))
                        continue

                    if member_path.exists():
                        continue

                    member_path.parent.mkdir(parents=True, exist_ok=True)
                    with tf.extractfile(member) as src, open(member_path, "wb") as dst:
                        dst.write(src.read())
                    extracted.append(str(member_path))

        return extracted
