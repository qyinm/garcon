
import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from garcon.executor import (
    EXECUTOR_RESULT_CLARIFICATION,
    EXECUTOR_RESULT_NEEDS_CONFIRMATION,
    EXECUTOR_RESULT_OK,
    EXECUTOR_RESULT_REFUSED,
    execute_action,
)
from garcon.model_manager import (
    MODEL_NAME,
    download_model,
    is_downloaded,
    model_path,
    model_size,
    remove_model,
)
from garcon.parser import parse_action
from garcon.router import route_with_rules
from garcon.safety import validate_action
from garcon.undo import get_latest, pop_latest

app = typer.Typer(
    name="garcon",
    help="Tiny local terminal coworker",
    no_args_is_help=True,
)
model_app = typer.Typer(help="Manage the local SLM model")
app.add_typer(model_app, name="model")

console = Console()


def handle(user_input: str) -> bool:
    raw = route_with_rules(user_input)

    action, err = parse_action(raw)
    if err:
        console.print(f"[red]오류: {err}[/red]")
        return True

    ok, reason = validate_action(action)
    if not ok:
        console.print(f"[red]차단됨: {reason}[/red]")
        return True

    result = execute_action(action, confirmed=False)

    result_type = result.get("type")

    if result_type == EXECUTOR_RESULT_REFUSED:
        console.print(f"[yellow]{result['message']}[/yellow]")
        return True

    if result_type == EXECUTOR_RESULT_CLARIFICATION:
        console.print(f"[cyan]{result['message']}[/cyan]")
        return True

    if result.get("message"):
        console.print(f"[green]{result['message']}[/green]")

    if result_type == EXECUTOR_RESULT_OK and result.get("data"):
        _display_result(action.skill if action else "", result["data"])

    if result_type == EXECUTOR_RESULT_NEEDS_CONFIRMATION:
        data = result.get("data") or {}

        plan_items = (
            data.get("plan")
            or data.get("entries")
            or data.get("results")
            or data.get("lines")
            or data.get("files")
            or []
        )

        if plan_items:
            console.print()
            for item in plan_items[:20]:
                if isinstance(item, dict):
                    label = (
                        item.get("name") or
                        item.get("file") or
                        item.get("path") or
                        item.get("from", "") +
                        (" -> " + item.get("to", "") if item.get("to") else "") or
                        str(item)
                    )
                    console.print(f"  [dim]•[/dim] {label}")
                elif isinstance(item, str):
                    console.print(f"  [dim]•[/dim] {item}")
                else:
                    console.print(f"  [dim]•[/dim] {item}")

            if len(plan_items) > 20:
                console.print(f"  [dim]... 외 {len(plan_items) - 20}개[/dim]")
        elif data:
            entries = data.get("entries", [])
            if entries:
                console.print()
                for e in entries[:20]:
                    console.print(f"  [dim]•[/dim] {e['name']}")
                if len(entries) > 20:
                    console.print(f"  [dim]... 외 {len(entries) - 20}개[/dim]")

        answer = typer.prompt("\n실행할까요?", default="n")
        if answer.lower() not in ("y", "yes", "네", "응", "예"):
            console.print("[yellow]취소했습니다.[/yellow]")
            return True

        confirmed_result = execute_action(action, confirmed=True)
        if confirmed_result.get("message"):
            console.print(f"[green]{confirmed_result['message']}[/green]")

        if confirmed_result.get("data"):
            _display_result(
                action.skill if action else "",
                confirmed_result["data"],
            )

    return True


def _display_result(skill_name: str, data: dict) -> None:
    if skill_name == "list_files":
        entries = data.get("entries", [])
        if not entries:
            return
        table = Table(show_header=True)
        table.add_column("이름", style="cyan")
        if "size" in entries[0]:
            table.add_column("크기", justify="right")
            table.add_column("종류")
        for e in entries:
            if "size" in e:
                size = e["size"]
                size_str = (
                    f"{size / 1024:.1f}KB" if size > 1024
                    else f"{size}B" if size >= 0
                    else "?"
                )
                kind = "디렉토리" if e.get("is_dir") else "파일"
                table.add_row(e["name"], size_str, kind)
            else:
                table.add_row(e["name"])
        console.print(table)

    elif skill_name == "read_file":
        lines = data.get("lines", [])
        if not lines:
            return
        for i, line in enumerate(lines, 1):
            console.print(f"{i:>4} {line}", markup=False)

    elif skill_name == "search_text":
        results = data.get("results", [])
        if not results:
            return
        for r in results:
            console.print(
                f"[dim]{r['file']}:{r['line']}[/dim]  {r['content']}",
                markup=False,
            )

    elif skill_name == "find_large_files":
        files = data.get("files", [])
        if not files:
            return
        table = Table(show_header=True)
        table.add_column("파일", style="cyan")
        table.add_column("크기", justify="right")
        for f in files:
            table.add_row(f["path"], f"{f['size_mb']}MB")
        console.print(table)

    elif skill_name == "organize_files":
        plan = data.get("plan", [])
        if not plan:
            return
        table = Table(show_header=True)
        table.add_column("이동 전", style="cyan")
        table.add_column("이동 후")
        for item in plan[:20]:
            table.add_row(item.get("from", ""), item.get("to", ""))
        if len(plan) > 20:
            table.add_row(f"... 외 {len(plan) - 20}개", "")
        console.print(table)

    elif skill_name == "rename_files":
        plan = data.get("plan", [])
        if not plan:
            return
        table = Table(show_header=True)
        table.add_column("변경 전", style="cyan")
        table.add_column("변경 후")
        for item in plan[:20]:
            table.add_row(item.get("from", ""), item.get("to", ""))
        if len(plan) > 20:
            table.add_row(f"... 외 {len(plan) - 20}개", "")
        console.print(table)

    elif skill_name == "compress_files":
        console.print(f"[dim]출력: {data.get('output', '')}[/dim]")

    elif skill_name == "extract_archive":
        console.print(f"[dim]대상: {data.get('target_dir', '')}[/dim]")


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
    entry = get_latest()
    if not entry:
        console.print("[yellow]취소 가능한 작업이 없습니다.[/yellow]")
        return

    undo_data = entry.get("undo", {})
    items = undo_data.get("items", [])
    skill = entry.get("skill", "unknown")
    op_id = entry.get("operation_id", "")

    console.print("[bold]최근 실행 취소 가능한 작업:[/bold]")
    console.print(f"  {skill} ({op_id}) — {len(items)}개 파일")

    for item in items[:10]:
        console.print(f"  [dim]•[/dim] {item.get('from', '')}")

    if len(items) > 10:
        console.print(f"  [dim]... 외 {len(items) - 10}개[/dim]")

    answer = typer.prompt("\n되돌릴까요?", default="n")
    if answer.lower() not in ("y", "yes", "네", "응", "예"):
        console.print("[yellow]취소했습니다.[/yellow]")
        return

    _execute_undo(entry)
    pop_latest()
    console.print("[green]작업을 되돌렸습니다.[/green]")


def _execute_undo(entry: dict):
    import shutil
    from pathlib import Path

    undo_data = entry.get("undo", {})
    undo_type = undo_data.get("type", "")
    items = undo_data.get("items", [])

    if undo_type == "move_files_back":
        for item in items:
            src = Path(item["from"]).expanduser()
            dst = Path(item["to"]).expanduser()
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))

    elif undo_type == "delete_archive":
        for item in items:
            path = Path(item.get("path", "")).expanduser()
            if path.exists():
                path.unlink()

    elif undo_type == "delete_files":
        for item in items:
            path = Path(item.get("path", "")).expanduser()
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(str(path))
                else:
                    path.unlink()


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
        console.print("[green]사용 가능[/green]")
        console.print(f"  경로: {model_path()}")
        console.print(f"  크기: {size_mb:.0f} MB")
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
