import click
import requests
from rich.console import Console
from rich.table import Table
from . import auth, config

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
        console.print(f"[red]✗[/red] {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        raise SystemExit(1)
    if creds is None:
        config.save_credentials(username, password)
    console.print(f"[green]✓[/green] Logged in as {display_name}")


@main.command()
def logout():
    remove = click.confirm(
        "Also remove saved credentials from keyring?", default=False
    )
    auth.logout(remove_keyring=remove)
    console.print("[green]✓[/green] Logged out")


@main.command()
@click.argument("problem", type=int)
@click.argument("answer")
def submit(problem, answer):
    from . import submit as submit_mod
    try:
        correct = submit_mod.submit_answer(problem, answer)
        if correct:
            console.print("[green]✓ Correct![/green]")
        else:
            console.print("[red]✗ Incorrect[/red]")
    except PermissionError:
        console.print("[yellow]Not logged in. Run `euler login` first.[/yellow]")
        raise SystemExit(1)
    except ValueError as e:
        console.print(f"[yellow]{e}[/yellow]")
        raise SystemExit(1)
    except requests.exceptions.RequestException as e:
        console.print(f"[red]✗[/red] Network error: {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
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
        console.print(f"[red]✗[/red] Network error: {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise SystemExit(1)
