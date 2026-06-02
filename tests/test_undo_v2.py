from pathlib import Path

from garcon.undo import (
    TRASH_DIR,
    UNDO_FILE,
    _read_log,
    _write_log,
    record_undo,
    trash_list,
    trash_restore,
    undo_last,
)


def _cleanup():
    if UNDO_FILE.exists():
        UNDO_FILE.unlink()
    if TRASH_DIR.exists():
        import shutil
        shutil.rmtree(str(TRASH_DIR))


def test_undo_with_no_history_returns_false():
    _cleanup()
    assert not undo_last()


def test_rm_undo_restores_file():
    _cleanup()
    test_dir = Path("tests/test_commands")
    test_file = test_dir / "test_undo_rm.txt"
    test_file.write_text("undo me")

    from garcon.commands.file_ops import execute_rm

    result = execute_rm(path=str(test_file))
    assert not test_file.exists()
    assert result.undo_info is not None

    record_undo("rm_command", {"path": str(test_file)}, result.undo_info)
    assert undo_last()
    assert test_file.exists()
    assert test_file.read_text() == "undo me"
    test_file.unlink(missing_ok=True)


def test_mv_undo_restores_original():
    _cleanup()
    test_dir = Path("tests/test_commands")
    src = test_dir / "test_undo_mv_src.txt"
    dst = test_dir / "test_undo_mv_dst.txt"
    src.write_text("movable")

    from garcon.commands.file_ops import execute_mv

    result = execute_mv(source=str(src), destination=str(dst))
    assert not src.exists()
    assert dst.exists()
    assert result.undo_info is not None

    record_undo("mv_command", {"source": str(src), "destination": str(dst)}, result.undo_info)
    assert undo_last()
    assert src.exists()
    assert src.read_text() == "movable"
    dst.unlink(missing_ok=True)
    src.unlink(missing_ok=True)


def test_chmod_undo_restores_mode():
    _cleanup()
    test_dir = Path("tests/test_commands")
    test_file = test_dir / "test_undo_chmod.txt"
    test_file.write_text("chmod test")
    original_mode = test_file.stat().st_mode

    from garcon.commands.permissions import execute_chmod

    result = execute_chmod(mode="755", path=str(test_file))
    assert result.undo_info is not None

    record_undo("chmod_command", {"mode": "755", "path": str(test_file)}, result.undo_info)
    assert undo_last()
    assert test_file.stat().st_mode == original_mode
    test_file.unlink(missing_ok=True)


def test_trash_dir_created_on_first_use():
    _cleanup()
    assert not TRASH_DIR.exists()
    test_dir = Path("tests/test_commands")
    test_file = test_dir / "test_trash_create.txt"
    test_file.write_text("trash test")

    from garcon.commands.file_ops import execute_rm
    result = execute_rm(path=str(test_file))
    record_undo("rm_command", {"path": str(test_file)}, result.undo_info)
    assert TRASH_DIR.exists()


def test_trash_list_shows_files():
    _cleanup()
    test_dir = Path("tests/test_commands")
    test_file = test_dir / "test_trash_list.txt"
    test_file.write_text("trash list test")

    from garcon.commands.file_ops import execute_rm
    result = execute_rm(path=str(test_file))
    record_undo("rm_command", {"path": str(test_file)}, result.undo_info)

    items = trash_list()
    assert len(items) > 0
    assert any("test_trash_list.txt" in item["original_name"] for item in items)


def test_trash_restore_specific_id():
    _cleanup()
    test_dir = Path("tests/test_commands")
    test_file = test_dir / "test_trash_restore.txt"
    test_file.write_text("trash restore test")

    from garcon.commands.file_ops import execute_rm
    result = execute_rm(path=str(test_file))
    record_undo("rm_command", {"path": str(test_file)}, result.undo_info)

    items = trash_list()
    assert len(items) > 0
    trash_id = items[0]["id"]
    assert trash_restore(trash_id)
    assert test_file.exists()
    assert test_file.read_text() == "trash restore test"
    test_file.unlink(missing_ok=True)


def test_old_records_rotated():
    _cleanup()
    _write_log([{"id": f"old_{i}"} for i in range(100)])
    log = _read_log()
    assert len(log) == 100

    record_undo("test_cmd", {}, {"type": "test", "items": []})
    log = _read_log()
    assert len(log) <= 100
