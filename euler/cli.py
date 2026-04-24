import sys
import click
import requests
from rich.console import Console
from rich.table import Table
from . import auth, config

# Force UTF-8 so unicode (superscripts, math symbols, box chars) renders on
# Windows consoles that default to cp1252. No-op on POSIX / already-UTF-8 streams.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console()


@click.group()
def main():
    pass


@main.command()
def login():
    creds = config.get_credentials()
    if creds is None:
        username = click.prompt("Username")
        password = click.prompt("Password", hide_input=True)
    else:
        username, password = creds
    try:
        display_name = auth.login(username, password)
    except ValueError as e:
        console.print(f"[red]x[/red] {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]x[/red] Unexpected error: {e}")
        raise SystemExit(1)
    if creds is None:
        config.save_credentials(username, password)
    console.print(f"[green]Logged in as {display_name}[/green]")


@main.command()
def logout():
    remove = click.confirm(
        "Also remove saved credentials from keyring?", default=False
    )
    auth.logout(remove_keyring=remove)
    console.print("[green]Logged out[/green]")


@main.command()
@click.argument("problem", type=int)
@click.argument("answer")
def submit(problem, answer):
    from . import submit as submit_mod
    try:
        result = submit_mod.submit_answer(problem, answer)
    except PermissionError:
        console.print("[yellow]Not logged in. Run `euler login` first.[/yellow]")
        raise SystemExit(1)
    except ValueError as e:
        console.print(f"[yellow]{e}[/yellow]")
        raise SystemExit(1)
    except requests.exceptions.RequestException as e:
        console.print(f"[red]x[/red] Network error: {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]x[/red] Error: {e}")
        raise SystemExit(1)
    if result == "correct":
        console.print("[green]Correct![/green]")
    elif result == "incorrect":
        console.print("[red]Incorrect[/red]")
    else:  # "blocked"
        console.print(
            "[yellow]Submission failed — PE did not process the answer "
            "(likely bot deflection; the response had no correct/incorrect marker).[/yellow]"
        )
        console.print("[dim]Details: ~/.euler/last_submit_debug.json[/dim]")
        raise SystemExit(1)


@main.command()
def status():
    from . import status as status_mod
    try:
        info = status_mod.get_status()
        table = Table()
        table.add_column("Username")
        table.add_column("Solved")
        table.add_column("Total")
        table.add_row(info["username"], str(info["solved"]), str(info["total"]))
        console.print(table)
    except PermissionError:
        console.print("[yellow]Not logged in. Run `euler login` first.[/yellow]")
        raise SystemExit(1)
    except requests.exceptions.RequestException as e:
        console.print(f"[red]x[/red] Network error: {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]x[/red] Error: {e}")
        raise SystemExit(1)


@main.command("get-problem")
@click.argument("problem", type=int)
def get_problem(problem):
    from rich.panel import Panel
    from . import problem as problem_mod
    try:
        text = problem_mod.get_problem_text(problem)
    except ValueError as e:
        console.print(f"[yellow]{e}[/yellow]")
        raise SystemExit(1)
    except requests.exceptions.RequestException as e:
        console.print(f"[red]x[/red] Network error: {e}")
        raise SystemExit(1)
    rendered = problem_mod.render_for_terminal(text)
    panel = Panel(
        rendered.strip(),
        title=f"[bold cyan]Problem {problem}[/bold cyan]",
        subtitle=f"[dim]projecteuler.net/problem={problem}[/dim]",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)
