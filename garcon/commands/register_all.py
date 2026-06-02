from garcon.commands import register
from garcon.commands.archive import execute_tar
from garcon.commands.content import (
    execute_cat,
    execute_diff,
    execute_head,
    execute_tail,
    execute_wc,
)
from garcon.commands.file_ops import (
    execute_cp,
    execute_ls,
    execute_mkdir,
    execute_mv,
    execute_rm,
    execute_tree,
)
from garcon.commands.permissions import execute_chmod
from garcon.commands.search import execute_find, execute_grep
from garcon.commands.text import execute_sort, execute_uniq


def register_all():
    commands = [
        ("ls_command", execute_ls, {"danger": "low", "creates_files": False, "modifies_files": False}),
        ("tree_command", execute_tree, {"danger": "low", "creates_files": False, "modifies_files": False}),
        ("cat_command", execute_cat, {"danger": "low", "creates_files": False, "modifies_files": False}),
        ("head_command", execute_head, {"danger": "low", "creates_files": False, "modifies_files": False}),
        ("tail_command", execute_tail, {"danger": "low", "creates_files": False, "modifies_files": False}),
        ("wc_command", execute_wc, {"danger": "low", "creates_files": False, "modifies_files": False}),
        ("grep_command", execute_grep, {"danger": "low", "creates_files": False, "modifies_files": False}),
        ("find_command", execute_find, {"danger": "low", "creates_files": False, "modifies_files": False}),
        ("sort_command", execute_sort, {"danger": "low", "creates_files": False, "modifies_files": False}),
        ("uniq_command", execute_uniq, {"danger": "low", "creates_files": False, "modifies_files": False}),
        ("diff_command", execute_diff, {"danger": "low", "creates_files": False, "modifies_files": False}),
        ("mkdir_command", execute_mkdir, {"danger": "low", "creates_files": True, "modifies_files": False}),
        ("cp_command", execute_cp, {"danger": "medium", "creates_files": True, "modifies_files": True}),
        ("mv_command", execute_mv, {"danger": "medium", "creates_files": False, "modifies_files": True}),
        ("rm_command", execute_rm, {"danger": "high", "creates_files": False, "modifies_files": True}),
        ("chmod_command", execute_chmod, {"danger": "high", "creates_files": False, "modifies_files": True}),
        ("tar_command", execute_tar, {"danger": "medium", "creates_files": True, "modifies_files": True}),
    ]

    for name, fn, safety in commands:
        register(name, fn, safety=safety)
