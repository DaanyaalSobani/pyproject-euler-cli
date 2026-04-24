import click
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
        config.save_credentials(username, password)
    else:
        username, password = creds
    try:
        display_name = auth.login(username, password)
        console.print(f"[green]✓[/green] Logged in as {display_name}")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        raise SystemExit(1)


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
    pass  # implemented in Task 7


@main.command()
def status():
    pass  # implemented in Task 8
