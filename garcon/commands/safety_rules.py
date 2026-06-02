from garcon.commands import register

READ_ONLY_COMMANDS = [
    "ls_command",
    "cat_command",
    "head_command",
    "tail_command",
    "wc_command",
    "grep_command",
    "find_command",
    "sort_command",
    "uniq_command",
    "diff_command",
    "tree_command",
]


def register_safety_rules():
    for name in READ_ONLY_COMMANDS:
        register(name, lambda **kw: None, safety={
            "danger": "low",
            "creates_files": False,
            "modifies_files": False,
        })
