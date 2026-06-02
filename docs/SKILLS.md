# Skills reference

## list_files

파일 목록을 표시합니다.

| Arg | Type | Default | Description |
|-----|------|---------|-------------|
| `path` | string | `"."` | Target directory |
| `hidden` | bool | `false` | Show hidden files |
| `detail` | bool | `false` | Show detailed info |

## read_file

파일 내용을 읽습니다.

| Arg | Type | Default | Description |
|-----|------|---------|-------------|
| `path` | string | — | File path |
| `max_lines` | int | `100` | Maximum lines to show |

## search_text

텍스트를 검색합니다.

| Arg | Type | Default | Description |
|-----|------|---------|-------------|
| `path` | string | `"."` | Search root directory |
| `query` | string | — | Search keyword |
| `include_extensions` | list | `null` | Filter by extension |
| `max_results` | int | `50` | Max results |
| `max_file_size` | int | `10MB` | Skip larger files |
| `max_scanned_files` | int | `5000` | Stop after scanning N files |

## find_large_files

큰 파일을 찾습니다.

| Arg | Type | Default | Description |
|-----|------|---------|-------------|
| `path` | string | `"."` | Search directory |
| `limit` | int | `20` | Max results |
| `min_size_mb` | int | `100` | Minimum file size in MB |

## organize_files

확장자별로 파일을 정리합니다.

| Arg | Type | Description |
|-----|------|-------------|
| `source_dir` | string | Source directory |
| `rules` | list | List of `{extensions, target_dir}` rules |

## rename_files

파일 이름을 변경합니다.

| Arg | Type | Description |
|-----|------|-------------|
| `source_dir` | string | Target directory |
| `pattern` | string | String to replace |
| `replacement` | string | Replacement string |

## compress_files

파일을 압축합니다. **zip only in v0.**

| Arg | Type | Description |
|-----|------|-------------|
| `paths` | list | Files to compress |
| `output` | string | Output path (`.zip` appended if missing) |

## extract_archive

압축을 해제합니다.

| Arg | Type | Default | Description |
|-----|------|---------|-------------|
| `archive` | string | — | Archive file path |
| `target_dir` | string | `"."` | Output directory |

### Safety

- Path traversal, symlinks, and hardlinks are rejected
- Existing files are never overwritten
- Max extract size: 500 MB
