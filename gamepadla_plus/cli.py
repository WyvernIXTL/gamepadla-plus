from tqdm import tqdm
import webbrowser
import pygame
import typer
from rich import print as rprint
from rich.markdown import Markdown

from .__init__ import VERSION
from .common import (
    get_joysticks,
    StickSelector,
    GamePadConnection,
    write_to_file,
    upload_data,
    test_execution,
    wrap_data_for_server,
    read_license,
)

app = typer.Typer(
    help="Gamepad latency and polling rate tester.",
)


@app.command()
def list():
    """
    List controller id's.
    """
    pygame.init()
    if joysticks := get_joysticks():
        rprint(f"[green]Found {len(joysticks)} controllers[/green]")

        for idx, joystick in enumerate(joysticks):
            rprint(f"[blue]{idx}.[/blue] [bold cyan]{joystick.get_name()}[/bold cyan]")
    else:
        rprint("[red]No controllers found.[/red]")


@app.command()
def test(
    out: str | None = typer.Option(help="Write result to file.", default=None),
    samples: int = typer.Option(help="How many samples are to be taken.", default=2000),
    stick: StickSelector = typer.Option(
        help="Choose which stick to test with.", default=StickSelector.LEFT
    ),
    upload: bool = typer.Option(
        help="Upload result to <gamepadla.com>?", default=False
    ),
    gamepad_name: str | None = typer.Option(help="Name of the game pad", default=None),
    gamepad_connection: GamePadConnection | None = typer.Option(
        help="How the game pad is connected.", default=None
    ),
    id: int = typer.Argument(
        help="Controller id. Check possible controllers with list command.", default=0
    ),
):
    """
    Test controller with id.
    """

    if upload and (gamepad_name is None or gamepad_connection is None):
        rprint("[red]Upload requires to set gamepad-name and gamepad-connection![/red]")
        exit(1)

    pygame.init()

    joysticks = get_joysticks()
    if not joysticks:
        rprint("[red]No controllers found.[/red]")
        exit(1)
    joystick = joysticks[id]

    with tqdm(
        total=samples,
        ncols=76,
        bar_format="{l_bar}{bar} | {postfix[0]}",
        postfix=[0],
    ) as pbar:

        def progress_bar_update(delay: float):
            pbar.update(1)
            pbar.postfix[0] = "{:05.2f} ms".format(delay)

        result = test_execution(
            samples=samples, stick=stick, joystick=joystick, tick=progress_bar_update
        )

    rprint(
        Markdown(
            f"""
| Parameter           | Value                         |
|---------------------|-------------------------------|
| Gamepad mode        | {result["joystick_name"]}     |
| Operating System    | {result["os_name"]}                     |
| Polling Rate Max.   | {result["max_polling_rate"]} Hz         |
| Polling Rate Avg.   | {result["polling_rate"]} Hz             |
| Stability           | {result["stablility"]}%                 |
|                     |                               |
| Minimal latency     | {result["filteredMin"]} ms              |
| Average latency     | {result["filteredAverage_rounded"]} ms  |
| Maximum latency     | {result["filteredMax"]} ms              |
| Jitter              | {result["jitter"]} ms                   |
"""
        )
    )

    data = wrap_data_for_server(result=result)

    if out is not None:
        try:
            write_to_file(data=data, path=out)
            rprint(f"[green]Wrote result to file {out}[/green]")
        except Exception as e:
            rprint(f"[red]Failed to write result to path {out}.[/red]")
            raise e

    if upload:
        try:
            upload_data(data=data, connection=gamepad_connection, name=gamepad_name)

            rprint("[green]Test results successfully sent to the server.[/green]")
            stamp = data["test_key"]
            webbrowser.open(f"https://gamepadla.com/result/{stamp}/")
        except Exception as e:
            rprint("[red]Failed to send test results to the server.[/red]")
            raise e


@app.command()
def version():
    rprint(VERSION)


@app.command()
def license():
    print(read_license())
