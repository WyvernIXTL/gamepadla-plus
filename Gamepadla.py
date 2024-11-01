ver = "1.2.0"

from typing_extensions import Annotated
import os
from enum import Enum

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

from colorama import Fore, Style
import time
import json
from tqdm import tqdm
import numpy as np
import platform
import requests
import uuid
import webbrowser
import pygame
import typer
from rich import print
from rich.markdown import Markdown

app = typer.Typer(
    no_args_is_help=True,
    help="Gamepad latency and polling rate tester.",
)


class StickSelector(str, Enum):
    left = "left"
    right = "right"


def get_joysticks() -> list | None:
    pygame.joystick.init()
    joysticks = [
        pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())
    ]
    delay_list = []

    if joysticks:
        return joysticks
    else:
        return None


@app.command()
def list():
    """
    List controller id's.
    """
    pygame.init()
    if joysticks := get_joysticks():
        print(f"[green]Found {len(joysticks)} controllers[/green]")

        for idx, joystick in enumerate(joysticks):
            print(f"[blue]{idx}.[/blue] [bold cyan]{joystick.get_name()}[/bold cyan]")
    else:
        print("[red]No controllers found.[/red]")


@app.command()
def test(
    out: str = typer.Option(help="Write result to file.", default=""),
    samples: int = typer.Option(help="How many samples are to be taken.", default=2000),
    stick: StickSelector = typer.Option(
        help="Choose which stick to test with.", default=StickSelector.left
    ),
    upload: bool = typer.Option(
        help="Upload result to <gamepadla.com>?", default=False
    ),
    id: int = typer.Argument(
        help="Controller id. Check possible controllers with list command.", default=0
    ),
):
    """
    Test controller with id.
    """

    pygame.init()

    def filter_outliers(array):
        """
        Function to filter out outliers in latency data.
        """
        lower_quantile = 0.02
        upper_quantile = 0.995

        sorted_array = sorted(array)
        lower_index = int(len(sorted_array) * lower_quantile)
        upper_index = int(len(sorted_array) * upper_quantile)

        return sorted_array[lower_index : upper_index + 1]

    joysticks = get_joysticks()
    if not joysticks:
        print("[red]No controllers where found.[/red]")
        exit(1)
    joystick = joysticks[id]

    joystick.init()  # Initialize the selected joystick
    joystick_name = joystick.get_name()

    if stick == StickSelector.left:
        axis_x = 0  # Axis for the left stick
        axis_y = 1
    elif stick == StickSelector.right:
        axis_x = 2  # Axis for the right stick
        axis_y = 3

    if not joystick.get_init():
        print("[red]Controller not connected[/red]")
        exit(1)

    times = []
    delay_list = []
    start_time = time.time()
    prev_x, prev_y = None, None

    # Main loop to gather latency data from joystick movements
    with tqdm(
        total=samples,
        ncols=76,
        bar_format="{l_bar}{bar} | {postfix[0]}",
        postfix=[0],
    ) as pbar:
        while True:
            pygame.event.pump()
            x = joystick.get_axis(axis_x)
            y = joystick.get_axis(axis_y)
            pygame.event.clear()

            # Ensure the stick has moved significantly (anti-drift)
            if not ("0.0" in str(x) and "0.0" in str(y)):
                if prev_x is None and prev_y is None:
                    prev_x, prev_y = x, y
                elif x != prev_x or y != prev_y:
                    end_time = time.time()
                    duration = round((end_time - start_time) * 1000, 2)
                    start_time = end_time
                    prev_x, prev_y = x, y

                    while True:
                        pygame.event.pump()
                        new_x = joystick.get_axis(axis_x)
                        new_y = joystick.get_axis(axis_y)
                        pygame.event.clear()

                        # If stick moved again, calculate delay
                        if new_x != x or new_y != y:
                            end = time.time()
                            delay = round((end - start_time) * 1000, 2)
                            if delay != 0.0 and delay > 0.2 and delay < 150:
                                times.append(delay * 1.057)  # Adjust for a 5% offset
                                pbar.update(1)
                                pbar.postfix[0] = "{:05.2f} ms".format(delay)
                                delay_list.append(delay)

                            break

                if len(times) >= samples:
                    break

    # Filter outliers from delay list
    delay_clear = delay_list
    delay_list = filter_outliers(delay_list)

    # Calculate statistical data
    filteredMin = min(delay_list)
    filteredMax = max(delay_list)
    filteredAverage = np.mean(delay_list)
    filteredAverage_rounded = round(filteredAverage, 2)

    polling_rate = round(1000 / filteredAverage, 2)
    jitter = round(np.std(delay_list), 2)

    # Function to determine max polling rate based on actual polling rate
    def get_polling_rate_max(actual_rate):
        max_rate = 125
        if actual_rate > 150:
            max_rate = 250
        if actual_rate > 320:
            max_rate = 500
        if actual_rate > 600:
            max_rate = 1000
        return max_rate

    os_name = platform.system()
    max_polling_rate = get_polling_rate_max(polling_rate)
    stablility = round((polling_rate / max_polling_rate) * 100, 2)

    print(
        Markdown(
            f"""
| Parameter           | Value                         |
|---------------------|-------------------------------|
| Gamepad mode        | {joystick_name}               |
| Operating System    | {os_name}                     |
| Polling Rate Max.   | {max_polling_rate} Hz         |
| Polling Rate Avg.   | {polling_rate} Hz             |
| Stability           | {stablility}%                 |
|                     |                               |
| Minimal latency     | {filteredMin} ms              |
| Average latency     | {filteredAverage_rounded} ms  |
| Maximum latency     | {filteredMax} ms              |
| Jitter              | {jitter} ms                   |
"""
        )
    )

    stamp = uuid.uuid4()
    uname = platform.uname()
    os_version = uname.version

    data = {
        "test_key": str(stamp),
        "version": ver,
        "url": "https://gamepadla.com",
        "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "driver": joystick_name,
        "os_name": os_name,
        "os_version": os_version,
        "min_latency": filteredMin,
        "avg_latency": filteredAverage_rounded,
        "max_latency": filteredMax,
        "polling_rate": polling_rate,
        "jitter": jitter,
        "mathod": "GP",
        "delay_list": ", ".join(map(str, delay_clear)),
    }

    if out != "":
        with open(out, "w") as outfile:
            json.dump(data, outfile, indent=4)
        print(f"[green]Wrote result to file {out}[/green]")

    if upload:
        gamepad_name = input("Please enter the name of your gamepad: ")
        connection = input(
            "Please select connection type (1. Cable, 2. Bluetooth, 3. Dongle): "
        )
        if connection == "1":
            connection = "Cable"
        elif connection == "2":
            connection = "Bluetooth"
        elif connection == "3":
            connection = "Dongle"
        else:
            print("Invalid choice. Defaulting to Cable.")
            connection = "Unset"

        # Add connection and gamepad name to the data
        data["connection"] = connection
        data["name"] = gamepad_name

        # Send test results to the server
        response = requests.post("https://gamepadla.com/scripts/poster.php", data=data)
        if response.status_code == 200:
            print("[green]Test results successfully sent to the server.[/green]")
            webbrowser.open(f"https://gamepadla.com/result/{stamp}/")
        else:
            print("[red]Failed to send test results to the server.[/red]")


def run():
    app()


if __name__ == "__main__":
    app()
