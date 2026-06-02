from pathlib import Path

from garcon.commands.archive import execute_tar
from garcon.commands.file_ops import execute_cp, execute_mkdir, execute_mv, execute_rm
from garcon.commands.permissions import execute_chmod

TEST_DIR = Path("tests/test_commands")


def test_mkdir_creates_directory():
    test_path = TEST_DIR / "test_mkdir_dir"
    try:
        result = execute_mkdir(path=str(test_path))
        assert result.success
        assert test_path.exists()
        assert test_path.is_dir()
    finally:
        if test_path.exists():
            test_path.rmdir()


def test_mkdir_on_existing_path_returns_error():
    # existing directory should succeed (mkdir -p)
    test_path = TEST_DIR / "test_mkdir_exists"
    test_path.mkdir(exist_ok=True)
    try:
        result = execute_mkdir(path=str(test_path))
        assert result.success
    finally:
        if test_path.exists():
            test_path.rmdir()


def test_cp_copies_file():
    src = TEST_DIR / "test_cp_src.txt"
    dst = TEST_DIR / "test_cp_dst.txt"
    src.write_text("hello")
    try:
        result = execute_cp(source=str(src), destination=str(dst))
        assert result.success
        assert dst.exists()
        assert dst.read_text() == "hello"
    finally:
        src.unlink(missing_ok=True)
        dst.unlink(missing_ok=True)


def test_cp_non_existent_source_returns_error():
    result = execute_cp(source="/nonexistent/file.txt", destination="/tmp/cp_test_dest.txt")
    assert not result.success


def test_mv_moves_file():
    src = TEST_DIR / "test_mv_src.txt"
    dst = TEST_DIR / "test_mv_dst.txt"
    src.write_text("movable content")
    try:
        result = execute_mv(source=str(src), destination=str(dst))
        assert result.success
        assert not src.exists()
        assert dst.exists()
        assert dst.read_text() == "movable content"
    finally:
        src.unlink(missing_ok=True)
        dst.unlink(missing_ok=True)


def test_mv_non_existent_source_returns_error():
    result = execute_mv(source="/nonexistent/file.txt", destination="/tmp/mv_test_dest.txt")
    assert not result.success


def test_rm_moves_file_to_trash():
    test_file = TEST_DIR / "test_rm_file.txt"
    test_file.write_text("to be trashed")
    assert test_file.exists()
    result = execute_rm(path=str(test_file))
    assert result.success
    assert "trash" in result.stdout
    assert not test_file.exists()


def test_rm_non_existent_file_returns_error():
    result = execute_rm(path="/nonexistent/file_xyzzy.txt")
    assert not result.success


def test_chmod_changes_permissions():
    test_file = TEST_DIR / "test_chmod_file.txt"
    test_file.write_text("chmod test")
    test_file.chmod(0o644)
    try:
        result = execute_chmod(mode="755", path=str(test_file))
        assert result.success
        mode = oct(test_file.stat().st_mode & 0o777)
        assert mode == "0o755"
    finally:
        test_file.chmod(0o644)
        test_file.unlink(missing_ok=True)


def test_rm_populates_undo_info():
    test_file = TEST_DIR / "test_undo_info.txt"
    test_file.write_text("undo test")
    result = execute_rm(path=str(test_file))
    assert result.success
    assert result.undo_info is not None
    assert result.undo_info["type"] == "restore_trash"
    assert len(result.undo_info["items"]) == 1
    assert not test_file.exists()


def test_read_only_commands_have_undo_info_none():
    from garcon.commands.file_ops import execute_ls
    result = execute_ls(path=str(TEST_DIR))
    assert result.undo_info is None


def test_tar_extract_safety():
    result = execute_tar(operation="extract", archive="nonexistent.tar.gz")
    assert not result.success
