import sys
import webbrowser
from typing import Annotated

import pygame
import typer
from rich import print as rprint
from rich.markdown import Markdown
from tqdm import tqdm

from gamepadla_plus.__init__ import (
    LICENSE_FILE_NAME,
    THIRD_PARTY_LICENSE_FILE_NAME,
    VERSION,
)
from gamepadla_plus.common import (
    GamePadConnection,
    StickSelector,
    TestResults,
    get_joysticks,
    read_license,
    test_execution,
    upload_data,
    wrap_data_for_server,
    write_to_file,
)

app = typer.Typer(
    help="Gamepad Polling Rate and Latency Testing Tool (CLI & GUI)",
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


def markdown_from_result(result: TestResults) -> Markdown:
    outlier_lower_avg_string = (
        f"{result['outlier_lower_avg']:.3f} ms"
        if result["outlier_lower_avg"] is not None
        else "no outliers"
    )
    outlier_upper_avg_string = (
        f"{result['outlier_upper_avg']:.3f} ms"
        if result["outlier_upper_avg"] is not None
        else "no outliers"
    )

    return Markdown(
        f"""
| Parameter           | Value                                       |
|---------------------|---------------------------------------------|
| Gamepad mode        | {result["joystick_name"]}                   |
| Operating System    | {result["os_name"]}                         |
| Polling Rate Avg.   | {result["polling_rate"]:.3f} Hz             |
|                     |                                             |
| Average latency     | {result["timings_filtered_avg"]:.3f} ms     |
| Minimal latency     | {result["timings_filtered_min"]:.3f} ms     |
| Maximum latency     | {result["timings_filtered_max"]:.3f} ms     |
| Jitter              | {result["jitter"]:.3f} ms                   |
|                     |                                             |
| Outlier lower Avg.  | {outlier_lower_avg_string}                  |
| Outlier lower %     | {result["outlier_lower_ratio"] * 100:.3f} % |
| Outlier upper Avg.  | {outlier_upper_avg_string}                  |
| Outlier upper %     | {result["outlier_upper_ratio"] * 100:.3f} % |
"""
    )


@app.command()
def test(
    out: Annotated[str | None, typer.Option(help="Write result to file.")] = None,
    samples: Annotated[
        int, typer.Option(help="How many samples are to be taken.")
    ] = 2000,
    stick: Annotated[
        StickSelector, typer.Option(help="Choose which stick to test with.")
    ] = StickSelector.LEFT,
    upload: Annotated[
        bool, typer.Option(help="Upload result to <gamepadla.com>?")
    ] = False,
    gamepad_name: Annotated[
        str | None, typer.Option(help="Name of the game pad")
    ] = None,
    gamepad_connection: Annotated[
        GamePadConnection | None, typer.Option(help="How the game pad is connected.")
    ] = None,
    id: Annotated[
        int,
        typer.Argument(
            help="Controller id. Check possible controllers with list command."
        ),
    ] = 0,
):
    """
    Test controller with id.
    """

    if upload and (gamepad_name is None or gamepad_connection is None):
        rprint("[red]Upload requires to set gamepad-name and gamepad-connection![/red]")
        sys.exit(1)

    pygame.init()

    joysticks = get_joysticks()
    if not joysticks:
        rprint("[red]No controllers found.[/red]")
        sys.exit(1)
    joystick = joysticks[id]

    with tqdm(
        total=samples,
        ncols=76,
        bar_format="{l_bar}{bar} | {postfix[0]}",
        postfix=[0],
    ) as pbar:

        def progress_bar_update(delay: float):
            pbar.update(1)
            pbar.postfix[0] = f"{delay:05.2f} ms"

        result = test_execution(
            sample_count=samples,
            stick_selected=stick,
            pygame_joystick=joystick,
            tick=progress_bar_update,
        )

    rprint(markdown_from_result(result))

    data = wrap_data_for_server(result=result)

    if out is not None:
        try:
            write_to_file(data=data, path=out)
            rprint(f"[green]Wrote result to file {out}[/green]")
        except Exception:
            rprint(f"[red]Failed to write result to path {out}.[/red]")
            raise

    if upload:
        # Keeping ty happy. Though it does not actually make any sense...
        if gamepad_name is None or gamepad_connection is None:
            sys.exit(1)

        try:
            upload_data(data=data, connection=gamepad_connection, name=gamepad_name)

            rprint("[green]Test results successfully sent to the server.[/green]")
            stamp = data["test_key"]
            webbrowser.open(f"https://gamepadla.com/result/{stamp}/")
        except Exception:
            rprint("[red]Failed to send test results to the server.[/red]")
            raise


@app.command()
def version():
    """
    Print version.
    """
    rprint(VERSION)


@app.command()
def license():
    """
    Print license of this project.
    """
    license = read_license(license_file_name=LICENSE_FILE_NAME)
    if license != "":
        print(license)
    else:
        rprint("[red]Failed to fetch license.[/red]")
        sys.exit(1)


@app.command()
def third_party_licenses():
    """
    Prints third party licenses.
    """
    licenses = read_license(license_file_name=THIRD_PARTY_LICENSE_FILE_NAME)
    if licenses != "":
        print(licenses)
    else:
        rprint("[red]Failed to fetch licenses.[/red]")
        sys.exit(1)
