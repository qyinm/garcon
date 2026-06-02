# Safety Model

garcon is a local file-system tool. This document describes the safety mechanisms that prevent accidental damage.

## Path policy

```
Blocked roots      →  /, /etc, /usr, /bin, /sbin, /System, /Library, /private, /var
Read zone          →  home directory, current working directory
Write zone         →  home directory, current working directory
```

Blocked roots are checked recursively — `/etc/passwd` is blocked because it is under `/etc`.

Read commands (`ls`, `cat`, `grep`, `find`) may access any path under the home directory or current working directory that is not under a blocked root.

Write commands (`cp`, `mv`, `rm`, `mkdir`, `tar`, `chmod`) are limited to the home directory and current working directory.

## Preview / confirm / undo

1. **Preview**: high-risk commands show a plan before execution, returning a list of planned changes
2. **Confirm**: the user types `y`, `yes`, `네`, or `응` to proceed
3. **Undo**: after execution, undo data is recorded. `garcon undo` reverses the last operation

### Undo types

| Undo type | What it does |
|-----------|-------------|
| `move_files_back` | Moves files back to their original locations |
| `delete_archive` | Deletes the created archive |
| `delete_files` | Deletes files that were created |

## Archive extraction safety

- Directory traversal via `..` or absolute paths in archive members is rejected
- Symlinks and hardlinks inside archives are rejected
- Existing files are never overwritten (skipped, excluded from undo)
- `MAX_EXTRACT_SIZE` limit: 500 MB

## Args scanning

All command arguments are scanned for path values before execution. `validate_command()` iterates over known path keys (`path`, `paths`, `source`, `destination`, `archive`, `files`, `name`) recursively through nested dicts and lists.

## Dangerous token detection

If command args contain shell-dangerous tokens (`rm -rf`, `sudo`, `chmod -R 777`, etc.), the action is rejected before any command runs.

## Limitation

garcon runs locally with no network access. It is not designed for multi-user environments or remote execution.
