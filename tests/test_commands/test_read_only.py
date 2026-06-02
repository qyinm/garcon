from pathlib import Path

import pytest

from garcon.commands import COMMANDS, execute_command, register
from garcon.commands.content import execute_cat, execute_diff, execute_head, execute_tail, execute_wc
from garcon.commands.file_ops import execute_ls, execute_tree
from garcon.commands.register_all import register_all
from garcon.commands.search import execute_find, execute_grep
from garcon.commands.text import execute_sort, execute_uniq

register_all()

TEST_DIR = Path("tests/test_commands")
TEST_FILE = TEST_DIR / "__init__.py"


def test_ls_lists_directory():
    result = execute_ls(path=str(TEST_DIR))
    assert result.success
    assert "__init__.py" in result.stdout


def test_ls_non_existent_path_returns_error():
    result = execute_ls(path="/nonexistent/path/12345")
    assert not result.success


def test_cat_reads_file():
    result = execute_cat(path=str(TEST_FILE))
    assert result.success


def test_cat_non_existent_file_returns_error():
    result = execute_cat(path="/nonexistent/file.txt")
    assert not result.success


def test_head_respects_lines():
    result = execute_head(path=str(TEST_FILE), lines=3)
    assert result.success
    assert len(result.stdout.split("\n")) <= 3


def test_tail_respects_lines():
    result = execute_tail(path=str(TEST_FILE), lines=3)
    assert result.success
    assert len(result.stdout.split("\n")) <= 3


def test_wc_counts_lines():
    test_path = TEST_DIR / "test_wc.txt"
    test_path.write_text("line1\nline2\nline3\n")
    result = execute_wc(path=str(test_path))
    assert result.success
    count = int(result.stdout.strip().split()[0])
    assert count == 3
    test_path.unlink(missing_ok=True)


def test_grep_finds_matching_lines():
    test_path = TEST_DIR / "test_grep_match.txt"
    test_path.write_text("hello world\ntest line\nfoo bar\n")
    result = execute_grep(pattern="test", path=str(test_path))
    assert result.success
    assert "test line" in result.stdout
    test_path.unlink(missing_ok=True)


def test_grep_no_matches_returns_empty():
    test_path = TEST_DIR / "test_grep_nomatch.txt"
    test_path.write_text("hello world\nfoo bar\n")
    result = execute_grep(pattern="XYZZYX_NONEXISTENT", path=str(test_path))
    # grep exit code 1 = no matches (not an error)
    assert result.stdout == ""
    test_path.unlink(missing_ok=True)


def test_find_finds_files():
    result = execute_find(path=str(TEST_DIR), name="*.py")
    assert result.success
    assert "__init__.py" in result.stdout


def test_find_no_matches_returns_empty():
    result = execute_find(path=str(TEST_DIR), name="*.nonexistent_ext_xyzzy")
    assert result.success


def test_sort_sorts_input():
    test_path = TEST_DIR / "test_unsorted.txt"
    if not test_path.exists():
        test_path.write_text("3\n1\n2\n")
    result = execute_sort(path=str(test_path))
    assert result.success
    lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
    assert lines == sorted(lines)
    test_path.unlink(missing_ok=True)


def test_uniq_deduplicates():
    test_path = TEST_DIR / "test_dup.txt"
    if not test_path.exists():
        test_path.write_text("a\na\nb\nb\nc\n")
    result = execute_uniq(path=str(test_path))
    assert result.success
    lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
    assert lines == ["a", "b", "c"]
    test_path.unlink(missing_ok=True)


def test_diff_compares_files():
    a = TEST_DIR / "test_diff_a.txt"
    b = TEST_DIR / "test_diff_b.txt"
    a.write_text("same\ndifferent_a\n")
    b.write_text("same\ndifferent_b\n")
    result = execute_diff(path1=str(a), path2=str(b))
    # diff returns exit code 1 when files differ (POSIX behavior)
    assert "different" in result.stdout or "different" in result.stderr
    assert not result.success  # exit code 1 = files differ
    a.unlink(missing_ok=True)
    b.unlink(missing_ok=True)


def test_tree_shows_directory():
    result = execute_tree(path=str(TEST_DIR))
    assert result.success
