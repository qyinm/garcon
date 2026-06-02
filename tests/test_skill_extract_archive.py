import io
import tarfile
import tempfile
import zipfile
from pathlib import Path

import pytest

from garcon.skills.extract_archive import ExtractArchiveSkill, safe_join


class TestSafeJoin:
    def test_safe_join_normal(self):
        base = Path("/tmp/out").resolve()
        result = safe_join(base, "file.txt")
        assert result == base / "file.txt"

    def test_safe_join_traversal(self):
        base = Path("/tmp/out")
        with pytest.raises(ValueError, match="안전하지 않은"):
            safe_join(base, "../../etc/passwd")

    def test_safe_join_absolute_member(self):
        base = Path("/tmp/out")
        with pytest.raises(ValueError, match="안전하지 않은"):
            safe_join(base, "/etc/passwd")


class TestExtractArchiveSkill:
    def test_nonexistent_archive(self):
        skill = ExtractArchiveSkill()
        result = skill.execute({
            "archive": "/nonexistent_xyz_archive.zip",
            "target_dir": ".",
        })
        assert result.ok is False

    def test_extract_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp, "test.zip")
            with zipfile.ZipFile(str(archive), "w") as zf:
                zf.writestr("file1.txt", "content1")
                zf.writestr("sub/file2.txt", "content2")
            target = Path(tmp, "out")
            skill = ExtractArchiveSkill()
            result = skill.execute({
                "archive": str(archive),
                "target_dir": str(target),
            })
            assert result.ok is True
            assert Path(target, "file1.txt").exists()
            assert Path(target, "sub", "file2.txt").exists()

    def test_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp, "test.zip")
            with zipfile.ZipFile(str(archive), "w") as zf:
                zf.writestr("file.txt", "content")
            skill = ExtractArchiveSkill()
            result = skill.preview({
                "archive": str(archive),
                "target_dir": str(Path(tmp, "out")),
            })
            assert result.ok is True

    def test_unsupported_format(self):
        skill = ExtractArchiveSkill()
        result = skill.execute({
            "archive": "/tmp/test.xyz",
            "target_dir": ".",
        })
        assert result.ok is False

    def test_undo_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp, "test.zip")
            with zipfile.ZipFile(str(archive), "w") as zf:
                zf.writestr("file.txt", "content")
            target = Path(tmp, "out")
            skill = ExtractArchiveSkill()
            result = skill.execute({
                "archive": str(archive),
                "target_dir": str(target),
            })
            assert result.ok is True
            assert result.undo is not None
            assert result.undo["type"] == "delete_files"
            assert any("file.txt" in item["path"] for item in result.undo["items"])

    def test_extract_zip_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp, "traversal.zip")
            with zipfile.ZipFile(str(archive), "w") as zf:
                zf.writestr("../../etc/passwd", "evil")
            target = Path(tmp, "out")
            skill = ExtractArchiveSkill()
            result = skill.execute({
                "archive": str(archive),
                "target_dir": str(target),
            })
            assert result.ok is False

    def test_extract_zip_existing_file_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            existing = Path(tmp, "out", "file.txt")
            existing.parent.mkdir(parents=True)
            existing.write_text("original", encoding="utf-8")

            archive = Path(tmp, "test.zip")
            with zipfile.ZipFile(str(archive), "w") as zf:
                zf.writestr("file.txt", "overwritten")
            target = Path(tmp, "out")
            skill = ExtractArchiveSkill()
            result = skill.execute({
                "archive": str(archive),
                "target_dir": str(target),
            })
            assert result.ok is True
            assert existing.read_text(encoding="utf-8") == "original"

    def test_extract_zip_undo_only_new_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            existing = Path(tmp, "out", "existing.txt")
            existing.parent.mkdir(parents=True)
            existing.write_text("keep", encoding="utf-8")

            archive = Path(tmp, "test.zip")
            with zipfile.ZipFile(str(archive), "w") as zf:
                zf.writestr("existing.txt", "overwritten")
                zf.writestr("new.txt", "new content")
            target = Path(tmp, "out")
            skill = ExtractArchiveSkill()
            result = skill.execute({
                "archive": str(archive),
                "target_dir": str(target),
            })
            assert result.ok is True
            undo_paths = [item["path"] for item in result.undo["items"]]
            assert any("new.txt" in p for p in undo_paths)
            assert not any("existing.txt" in p for p in undo_paths)

    def test_extract_tar_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp, "sym.tar")
            with tarfile.open(str(archive), "w") as tf:
                info = tarfile.TarInfo(name="link")
                info.type = tarfile.SYMTYPE
                info.linkname = "/etc/passwd"
                tf.addfile(info)
            target = Path(tmp, "out")
            skill = ExtractArchiveSkill()
            result = skill.execute({
                "archive": str(archive),
                "target_dir": str(target),
            })
            assert result.ok is False

    def test_extract_tar_hardlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            inner = Path(tmp, "real.txt")
            inner.write_text("data", encoding="utf-8")

            archive = Path(tmp, "hard.tar")
            with tarfile.open(str(archive), "w") as tf:
                tf.add(str(inner), "real.txt")
                info = tarfile.TarInfo(name="link")
                info.type = tarfile.LNKTYPE
                info.linkname = "real.txt"
                tf.addfile(info)
            target = Path(tmp, "out")
            skill = ExtractArchiveSkill()
            result = skill.execute({
                "archive": str(archive),
                "target_dir": str(target),
            })
            assert result.ok is False

    def test_extract_tar_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp, "traverse.tar")
            with tarfile.open(str(archive), "w") as tf:
                info = tarfile.TarInfo(name="../../etc/passwd")
                info.type = tarfile.REGTYPE
                info.size = 4
                tf.addfile(info, io.BytesIO(b"data"))
            target = Path(tmp, "out")
            skill = ExtractArchiveSkill()
            result = skill.execute({
                "archive": str(archive),
                "target_dir": str(target),
            })
            assert result.ok is False

    def test_extract_zip_absolute_path_member(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp, "abs.zip")
            with zipfile.ZipFile(str(archive), "w") as zf:
                zf.writestr("/etc/passwd", "evil")
            target = Path(tmp, "out")
            skill = ExtractArchiveSkill()
            result = skill.execute({
                "archive": str(archive),
                "target_dir": str(target),
            })
            assert result.ok is False
