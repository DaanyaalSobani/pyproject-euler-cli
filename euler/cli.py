import click
from . import auth

@click.group()
def main():
    print('hello')

@main.command()
def login():
    auth.test()
    pass

@main.command()

def status():
    pass

@main.command()
@click.argument("problem", type=int)
@click.argument("answer")
def submit(problem, answer):
    pass

@main.command()
def logout():
    pass