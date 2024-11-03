import typer

from .cli import app
from .gui import gui


@app.callback(invoke_without_command=True)
def start_gui(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        gui()


def run():
    app()


if __name__ == "__main__":
    app()
