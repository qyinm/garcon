
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from garcon.executor import execute_single_step
from garcon.model_manager import (
    MODEL_NAME,
    MODEL_MANIFEST,
    checksum_status,
    download_model,
    is_downloaded,
    model_path,
    model_size,
    remove_model,
)
from garcon.model_router import router as model_router
from garcon.undo import TRASH_DIR, undo_last
from garcon.undo import trash_list as undo_trash_list
from garcon.undo import trash_restore as undo_trash_restore

app = typer.Typer(
    name="garcon",
    help="Tiny local terminal coworker — Linux commands + agent loop",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)
model_app = typer.Typer(help="Manage the local SLM model")
app.add_typer(model_app, name="model")

console = Console()


COMMAND_ALIASES = {
    "ls": "ls_command", "cat": "cat_command", "head": "head_command",
    "tail": "tail_command", "wc": "wc_command", "grep": "grep_command",
    "find": "find_command", "mkdir": "mkdir_command", "rm": "rm_command",
    "cp": "cp_command", "mv": "mv_command", "cd": "cd_command",
    "chmod": "chmod_command", "tar": "tar_command", "zip": "tar_command",
    "unzip": "tar_command", "sort": "sort_command", "uniq": "uniq_command",
    "diff": "diff_command", "tree": "tree_command",
    "list": "ls_command", "delete": "rm_command", "copy": "cp_command",
    "move": "mv_command", "search": "grep_command", "compare": "diff_command",
    "rename": "mv_command", "md": "mkdir_command",
}


def _parse_direct(command: str, rest: str) -> tuple[str, dict] | None:
    action = COMMAND_ALIASES.get(command)
    if not action:
        return None

    from garcon.commands import COMMANDS
    fn = COMMANDS.get(action)
    if not fn:
        return None

    import inspect
    sig = inspect.signature(fn)
    params: dict[str, str | int | bool] = {}
    rest = rest.strip()

    for name, param in sig.parameters.items():
        if name == "path" and rest and not rest.startswith("-"):
            params["path"] = rest.split()[0]
            rest = rest[len(params["path"]):].strip()
        elif name == "source" and rest:
            parts = rest.split(None, 1)
            if parts:
                params["source"] = parts[0]
                rest = rest[len(parts[0]):].strip()
        elif name == "destination" and rest:
            parts = rest.split(None, 1)
            if parts:
                params["destination"] = parts[0]
                rest = rest[len(parts[0]):].strip()
        elif name == "pattern" and rest:
            parts = rest.split(None, 1)
            if parts:
                params["pattern"] = parts[0]
                rest = rest[len(parts[0]):].strip()
        elif name == "name" and rest:
            parts = rest.split(None, 1)
            if parts:
                params["name"] = parts[0]
                rest = rest[len(parts[0]):].strip()
        elif name == "options" and rest:
            params["options"] = rest.strip()
        elif name == "lines" and rest:
            try:
                params["lines"] = int(rest.split()[0])
                rest = ""
            except (ValueError, IndexError):
                params["lines"] = 10
        elif name == "mode" and rest:
            parts = rest.split(None, 1)
            if parts:
                params["mode"] = parts[0]
                rest = ""
        elif name == "archive" and rest:
            parts = rest.split(None, 1)
            if parts:
                params["archive"] = parts[0]
                rest = rest[len(parts[0]):].strip()
        elif name == "files" and rest:
            params["files"] = rest.strip()
            rest = ""
        elif name == "recursive":
            params["recursive"] = "-r" in rest or "-rf" in rest or "--recursive" in rest

    return action, params


def _parse_nl(user_input: str) -> dict | None:
    mp = model_path()
    if mp:
        from garcon.model_router import router as model_router
        result = model_router(user_input, mp)
        if result:
            return result

    parts = user_input.strip().split(None, 1)
    if not parts:
        return None
    parsed = _parse_direct(parts[0], parts[1] if len(parts) > 1 else "")
    if parsed:
        action, params = parsed
        return {"action": action, "params": params}

    return None


def handle(user_input: str) -> bool:
    result = _parse_nl(user_input)
    if not result:
        console.print("[yellow]요청을 이해하지 못했습니다. 다른 방식으로 다시 입력해보세요.[/yellow]")
        return True

    action = result.get("action", "")
    params = result.get("params", {})

    if action == "Finish":
        answer = params.get("final_answer", "")
        if answer:
            console.print(f"[cyan]{answer}[/cyan]")
        return True

    cmd_name = action.replace("_command", "")
    preview_parts = [cmd_name]
    for k, v in params.items():
        if v:
            preview_parts.append(f"{k}={v}")
    preview = " ".join(preview_parts)

    console.print(f"\n[bold cyan]🔍 실행:[/bold cyan] {preview}")

    exec_result = execute_single_step(action, params)
    if not exec_result["success"]:
        console.print(f"[red]⛔ {exec_result.get('error', '알 수 없는 오류')}[/red]")
        return True

    cmd_result = exec_result["result"]
    if cmd_result.stdout:
        console.print(cmd_result.stdout[:2000])
    if cmd_result.stderr:
        console.print(f"[red]{cmd_result.stderr[:500]}[/red]")

    console.print("[green]✅ 완료[/green]")
    return True


@app.command()
def chat():
    """Start interactive chat mode."""
    console.print(
        "[bold cyan]garcon[/bold cyan]"
        " — 파일 목록, 읽기, 검색, 정리를 도와드려요."
    )
    console.print("종료하려면 [bold]exit[/bold] 또는 [bold]quit[/bold] 입력\n")

    while True:
        user_input = typer.prompt("> ", prompt_suffix=" ")
        if user_input.strip().lower() in ("exit", "quit", "종료"):
            console.print("[green]garcon을 종료합니다.[/green]")
            break

        if not user_input.strip():
            continue

        handle(user_input)
        console.print()


@app.command()
def run(request: list[str] = typer.Argument(None)):
    """Run garcon with a single request (one-shot mode)."""
    if not request:
        console.print("[yellow]사용법: garcon run <자연어 요청>[/yellow]")
        console.print("예: garcon run 현재 폴더 파일 목록 보여줘")
        raise typer.Exit()

    user_input = " ".join(request)
    handle(user_input)


@app.command()
def undo():
    """Undo the most recent reversible operation."""
    if undo_last():
        console.print("[green]마지막 작업을 되돌렸습니다.[/green]")
    else:
        console.print("[yellow]취소 가능한 작업이 없습니다.[/yellow]")


@app.command()
def trash_list():
    """List files in the trash."""
    items = undo_trash_list()
    if not items:
        console.print("[yellow]휴지통이 비어 있습니다.[/yellow]")
        return

    table = Table(show_header=True)
    table.add_column("ID")
    table.add_column("파일")
    table.add_column("경로")
    seen = set()
    for item in items:
        key = item["id"]
        if key not in seen:
            table.add_row(item["id"][:8], item["original_name"], item["trash_path"])
            seen.add(key)
    console.print(table)


@app.command()
def trash_restore(id: str = typer.Argument(..., help="Trash item ID to restore")):
    """Restore a file from trash by ID."""
    if undo_trash_restore(id):
        console.print(f"[green]{id} 항목을 복원했습니다.[/green]")
    else:
        console.print(f"[red]{id} 항목을 찾을 수 없습니다.[/red]")


@model_app.command()
def download():
    """Download the SLM model (~105 MB)."""
    if is_downloaded():
        console.print("[yellow]모델이 이미 다운로드되어 있습니다.[/yellow]")
        console.print(f"  경로: {model_path()}")
        return

    console.print(f"[cyan]{MODEL_NAME}[/cyan] 모델을 다운로드합니다...")

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("다운로드 중...", total=100)

        def on_progress(pct):
            progress.update(task, completed=pct)

        download_model(progress_callback=on_progress)

    console.print("[green]완료![/green]")
    console.print(f"  경로: {model_path()}")


@model_app.command()
def status():
    """Show model download status."""
    if is_downloaded():
        size_mb = model_size() / 1024 / 1024
        cs = checksum_status()
        cs_display = {
            "verified": "[green]확인됨[/green]",
            "unknown": "[yellow]알 수 없음[/yellow]",
            "mismatch": "[red]불일치[/red]",
            "not_downloaded": "[dim]-[/dim]",
        }.get(cs, cs)
        console.print("[green]사용 가능[/green]")
        console.print(f"  경로: {model_path()}")
        console.print(f"  크기: {size_mb:.0f} MB")
        console.print(f"  SHA256: {cs_display}")
        console.print(f"  레포: {MODEL_MANIFEST['repo']}")
    else:
        console.print("[yellow]모델이 다운로드되지 않았습니다.[/yellow]")
        console.print("  다음 명령어로 다운로드: [bold]garcon model download[/bold]")


@model_app.command()
def remove():
    """Remove the downloaded model."""
    if not is_downloaded():
        console.print("[yellow]모델 파일이 없습니다.[/yellow]")
        return

    removed = remove_model()
    if removed:
        console.print("[green]모델 파일을 삭제했습니다.[/green]")
    else:
        console.print("[red]삭제 실패[/red]")


if __name__ == "__main__":
    app()
