import zipfile
from pathlib import Path

from garcon.skills.base import Skill, SkillResult


class CompressFilesSkill(Skill):
    name = "compress_files"
    risk = "medium"
    dry_run_supported = True

    def preview(self, args: dict) -> SkillResult:
        paths = args.get("paths", [])
        output = args.get("output", "")

        if not paths:
            return SkillResult(ok=False, message="압축할 파일이 지정되지 않았습니다.")

        if not output:
            return SkillResult(
                ok=False, message="출력 파일 경로가 지정되지 않았습니다."
            )

        resolved = []
        missing = []
        for p in paths:
            pp = Path(p).expanduser().resolve()
            if pp.exists():
                resolved.append(str(pp))
            else:
                missing.append(p)

        if missing:
            return SkillResult(
                ok=False,
                message=f"찾을 수 없는 파일: {', '.join(missing)}",
            )

        return SkillResult(
            ok=True,
            message=f"{len(resolved)}개 파일을 {output}로 압축합니다.",
            data={"plan": [{"file": p} for p in resolved], "output": output},
        )

    def execute(self, args: dict) -> SkillResult:
        paths = args.get("paths", [])
        output = Path(args.get("output", "")).expanduser().resolve()

        if not paths:
            return SkillResult(ok=False, message="압축할 파일이 지정되지 않았습니다.")

        if not output:
            return SkillResult(
                ok=False, message="출력 파일 경로가 지정되지 않았습니다."
            )

        if output.exists():
            return SkillResult(ok=False, message=f"이미 존재하는 파일입니다: {output}")

        resolved = []
        for p in paths:
            pp = Path(p).expanduser().resolve()
            if not pp.exists():
                return SkillResult(ok=False, message=f"파일을 찾을 수 없습니다: {p}")
            resolved.append(pp)

        output.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(str(output), "w", zipfile.ZIP_DEFLATED) as zf:
            for fp in resolved:
                if fp.is_dir():
                    for f in fp.rglob("*"):
                        zf.write(str(f), str(f.relative_to(fp.parent)))
                else:
                    zf.write(str(fp), fp.name)

        compressed = [str(p) for p in resolved]

        return SkillResult(
            ok=True,
            message=f"{len(resolved)}개 파일을 {output}로 압축했습니다.",
            data={"compressed": compressed, "output": str(output)},
            undo={
                "type": "delete_archive",
                "items": [{"path": str(output)}],
            },
        )
