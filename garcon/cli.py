from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from garcon.executor import (
    EXECUTOR_RESULT_CLARIFICATION,
    EXECUTOR_RESULT_NEEDS_CONFIRMATION,
    EXECUTOR_RESULT_OK,
    EXECUTOR_RESULT_REFUSED,
    execute_action,
)
from garcon.parser import parse_action
from garcon.router import route_with_rules
from garcon.safety import validate_action

app = typer.Typer(
    name="garcon",
    help="Tiny local terminal coworker",
    no_args_is_help=True,
)

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

        plan_items = (data.get("plan") or data.get("entries") or
                      data.get("results") or data.get("lines") or [])

        if plan_items:
            console.print()
            for item in plan_items[:20]:
                if isinstance(item, dict):
                    name = item.get("name", item.get("file", str(item)))
                    console.print(f"  [dim]•[/dim] {name}")
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


@app.command()
def chat():
    """Start interactive chat mode."""
    console.print("[bold cyan]garcon[/bold cyan] — 파일 목록, 읽기, 검색을 도와드려요.")
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


if __name__ == "__main__":
    app()
