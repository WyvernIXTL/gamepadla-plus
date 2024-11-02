from typing import Callable
import os
from enum import Enum

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

import time
import json
from tqdm import tqdm
import numpy as np
import platform
import requests
import uuid
import webbrowser
import pygame
from pygame.joystick import JoystickType
import typer
from rich import print as rprint
from rich.markdown import Markdown
from rich.traceback import install as traceback_install
import FreeSimpleGUI as sg

from .__init__ import __version__

LICENSE_FILE_NAME = "LICENSE.txt"
VERSION = f"gamepadla-plus {__version__}"


class StickSelector(str, Enum):
    LEFT = "left"
    RIGHT = "right"


class GamePadConnection(str, Enum):
    CABLE = "Cable"
    BLUETOOTH = "Bluetooth"
    DONGLE = "Dongle"


class GamepadlaError(Exception):
    pass


def get_joysticks() -> list[JoystickType] | None:
    """
    Returns a list of gamepads...

    Pygame NEEDS to be initalized firstm.
    """
    pygame.joystick.init()
    joysticks = [
        pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())
    ]

    if joysticks:
        return joysticks
    else:
        return None


def get_polling_rate_max(actual_rate: int) -> int:
    """
    Function to determine max polling rate based on actual polling rate
    """
    max_rate = 125
    if actual_rate > 150:
        max_rate = 250
    if actual_rate > 320:
        max_rate = 500
    if actual_rate > 600:
        max_rate = 1000
    return max_rate


def filter_outliers(array: list[float]) -> list[float]:
    """
    Function to filter out outliers in latency data.
    """
    lower_quantile = 0.02
    upper_quantile = 0.995

    sorted_array = sorted(array)
    lower_index = int(len(sorted_array) * lower_quantile)
    upper_index = int(len(sorted_array) * upper_quantile)

    return sorted_array[lower_index : upper_index + 1]


def test_execution(
    samples: int,
    stick: StickSelector,
    joystick: JoystickType,
    tick: Callable[[float], None],
) -> dict:
    """
    Executes the testing algorithm.

    Pygame NEEDS to be initalized firstm.
    """
    joystick.init()  # Initialize the selected joystick
    joystick_name = joystick.get_name()

    if stick == StickSelector.LEFT:
        axis_x = 0  # Axis for the left stick
        axis_y = 1
    elif stick == StickSelector.RIGHT:
        axis_x = 2  # Axis for the right stick
        axis_y = 3

    if not joystick.get_init():
        raise GamepadlaError("Controller not connected")

    times: list[float] = []
    delay_list: list[float] = []
    start_time: float = time.time()
    prev_x: float | None = None
    prev_y: float | None = None

    # Main loop to gather latency data from joystick movements
    while len(times) < samples:
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
                            tick(delay)
                            delay_list.append(delay)

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

    os_name = platform.system()
    max_polling_rate = get_polling_rate_max(polling_rate)
    stablility = round((polling_rate / max_polling_rate) * 100, 2)

    return {
        "joystick_name": joystick_name,
        "os_name": os_name,
        "max_polling_rate": max_polling_rate,
        "polling_rate": polling_rate,
        "stablility": stablility,
        "filteredMin": filteredMin,
        "filteredAverage_rounded": filteredAverage_rounded,
        "filteredMax": filteredMax,
        "jitter": jitter,
        "delay_clear": delay_clear,
    }


def wrap_data_for_server(result: dict) -> dict:
    """
    Wraps the test result struct into another struct for compatiblity.
    """
    stamp = uuid.uuid4()
    uname = platform.uname()
    os_version = uname.version

    return {
        "test_key": str(stamp),
        "version": __version__,
        "url": "https://gamepadla.com",
        "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "driver": result["joystick_name"],
        "os_name": result["os_name"],
        "os_version": os_version,
        "min_latency": result["filteredMin"],
        "avg_latency": result["filteredAverage_rounded"],
        "max_latency": result["filteredMax"],
        "polling_rate": result["polling_rate"],
        "jitter": result["jitter"],
        "mathod": "GP",
        "delay_list": ", ".join(map(str, result["delay_clear"])),
    }


def upload_data(data: dict, connection: GamePadConnection, name: str) -> bool:
    """
    Uploads results to server.
    """
    # Add connection and gamepad name to the data
    data["connection"] = connection.value
    data["name"] = name

    # Send test results to the server
    response = requests.post("https://gamepadla.com/scripts/poster.php", data=data)

    return response.status_code == 200


def write_to_file(data: dict, path: str):
    """
    Writes result to file.
    """
    with open(path, "w") as outfile:
        json.dump(data, outfile, indent=4)


app = typer.Typer(
    no_args_is_help=True,
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


def read_license() -> str:
    src_path = os.path.dirname(os.path.realpath(__file__))
    license_path = src_path + "/../" + LICENSE_FILE_NAME
    with open(license_path, "r") as license_file:
        license_text = license_file.read()
    return license_text


@app.command()
def license():
    print(read_license())


def run():
    app()


def error_popup(msg: str):
    sg.Window("Error", [[sg.Text(msg)], [sg.Push(), sg.Button("Continue")]]).read(
        close=True
    )


def license_popup():
    sg.Window(
        "Error", [[sg.Text(read_license())], [sg.Push(), sg.Button("Continue")]]
    ).read(close=True)


def upload_popup(data: dict):
    window = sg.Window(
        "Upload",
        [
            [sg.Text("Connection Type")],
            [
                sg.Radio(
                    GamePadConnection.DONGLE.value,
                    group_id=3,
                    default=True,
                    key="-RADIO-CONNECTION-DONGLE-",
                )
            ],
            [
                sg.Radio(
                    GamePadConnection.CABLE.value,
                    group_id=3,
                    default=False,
                    key="-RADIO-CONNECTION-CABLE-",
                )
            ],
            [
                sg.Radio(
                    GamePadConnection.BLUETOOTH.value,
                    group_id=3,
                    default=False,
                    key="-RADIO-CONNECTION-BLUETOOTH-",
                )
            ],
            [sg.Text("Gamepad Name")],
            [sg.Input(key="-CONTROLLER-NAME-INPUT-")],
            [sg.Push(), sg.Button("Cancel"), sg.Button("Upload")],
        ],
        finalize=True,
    )

    def get_connection_type() -> GamePadConnection:
        if window["-RADIO-CONNECTION-DONGLE-"].get():
            return GamePadConnection.DONGLE
        elif window["-RADIO-CONNECTION-CABLE-"].get():
            return GamePadConnection.CABLE
        elif window["-RADIO-CONNECTION-BLUETOOTH-"].get():
            return GamePadConnection.BLUETOOTH
        else:
            raise Exception("No valid connection choosen.")

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == "Cancel":
            break

        elif event == "Upload":
            connection_type = get_connection_type()
            controller_name = window["-CONTROLLER-NAME-INPUT-"].get()
            if upload_data(
                data=data,
                name=controller_name,
                connection=connection_type,
            ):
                stamp = data["test_key"]
                webbrowser.open(f"https://gamepadla.com/result/{stamp}/")
                break
            else:
                error_popup("Failed uploading results.")

    window.close()


def gui():
    traceback_install()
    pygame.init()
    joysticks: list[JoystickType] = []
    selected_joystick = 0
    data = {}
    count = 0

    layout = [
        [
            sg.Push(),
            sg.Button("Licenses", key="-SHOW-LICENSES-BUTTON-"),
        ],
        [
            sg.Listbox(
                [],
                key="-GAMEPAD-LIST-",
                enable_events=True,
                select_mode="LISTBOX_SELECT_MODE_SINGLE",
                size=(200, 4),
            ),
        ],
        [
            sg.Button("Refresh", key="-REFRESH-JOYSTICKS-BUTTON-", size=200),
        ],
        [
            [
                sg.Text("Samples:"),
                sg.Push(),
                sg.Radio("2000", group_id=1, default=True, key="-SAMPLE-RADIO-2000-"),
                sg.Radio("3000", group_id=1, default=False, key="-SAMPLE-RADIO-3000-"),
                sg.Radio("4000", group_id=1, default=False, key="-SAMPLE-RADIO-4000-"),
            ],
        ],
        [
            [
                sg.Text("Stick:"),
                sg.Push(),
                sg.Radio("left", group_id=2, default=True, key="-STICK-RADIO-LEFT-"),
                sg.Radio(
                    "right",
                    group_id=2,
                    default=False,
                    key="-STICK-RADIO-RIGHT-",
                ),
            ],
        ],
        [
            sg.Button("Test", key="-START-TEST-BUTTON-", size=200),
        ],
        [
            sg.Text(
                "Please rotate the stick of your gamepad slowly and steadily.",
                key="-TEST-INSTRUCTION-",
                visible=False,
            ),
        ],
        [
            sg.ProgressBar(
                12000, key="-PROGRESS-BAR-", visible=False, size_px=(300, 3)
            ),
            sg.Text("", key="-DELAY-OUTPUT-", visible=False),
        ],
        [sg.VPush()],
        [
            sg.Table(
                ["", ""],
                headings=["Parameter", "Value"],
                key="-RESULT-TABLE-",
                def_col_width=20,
                auto_size_columns=False,
                max_col_width=100,
                num_rows=10,
                hide_vertical_scroll=True,
                justification="left",
            )
        ],
        [
            sg.Button("Upload Result", disabled=True, key="-UPLOAD-BUTTON-", size=200),
        ],
        [
            sg.FileSaveAs(
                "Save to File",
                disabled=True,
                key="-SAVE-BUTTON-",
                size=200,
                default_extension="json",
                enable_events=True,
            ),
        ],
    ]

    window = sg.Window("Gamepadla+", layout, finalize=True, size=(400, 560))

    def update_joysticks():
        nonlocal joysticks
        if new_joysticks := get_joysticks():
            joysticks = new_joysticks
            joystick_names = [
                f"{i}. {j.get_name()}" for (i, j) in enumerate(new_joysticks)
            ]
            window["-GAMEPAD-LIST-"].update(joystick_names)
        else:
            joysticks = []
            window["-GAMEPAD-LIST-"].update([])

    update_joysticks()

    def get_sample_count() -> int:
        if window["-SAMPLE-RADIO-2000-"].get():
            return 2000
        if window["-SAMPLE-RADIO-3000-"].get():
            return 3000
        if window["-SAMPLE-RADIO-4000-"].get():
            return 4000

    def get_stick() -> StickSelector:
        if window["-STICK-RADIO-LEFT-"].get():
            return StickSelector.LEFT
        if window["-STICK-RADIO-RIGHT-"].get():
            return StickSelector.RIGHT

    def toggle_progress_bar(on: bool):
        window["-PROGRESS-BAR-"].update(visible=on)
        window["-DELAY-OUTPUT-"].update(visible=on)
        window["-TEST-INSTRUCTION-"].update(visible=on)

    def reset_progress_bar():
        nonlocal count
        window["-PROGRESS-BAR-"].update(current_count=0)
        window["-DELAY-OUTPUT-"].update("")
        count = 0

    def update_progress_bar(delay: float):
        nonlocal count
        count += 1
        factor = {
            2000: 6,
            3000: 4,
            4000: 3,
        }
        window["-PROGRESS-BAR-"].update(current_count=(count * factor[samples]))
        window["-DELAY-OUTPUT-"].update("{:05.2f} ms".format(delay))

    def update_result_table(data: dict):
        window["-RESULT-TABLE-"].update(
            [
                ["Gamepad mode", data["joystick_name"]],
                ["Operating System", data["os_name"]],
                ["Polling Rate Max.", f"{data['max_polling_rate']} Hz"],
                ["Polling Rate Avg.", f"{data['polling_rate']} Hz"],
                ["Stability", f"{data['stablility']}%"],
                ["", ""],
                ["Minimal latency", f"{data['filteredMin']} ms"],
                ["Average latency", f"{data['filteredAverage_rounded']} ms"],
                ["Maximum latency", f"{data['filteredMax']} ms"],
                ["Jitter", f"{data['jitter']} ms"],
            ]
        )

    while True:
        window["-START-TEST-BUTTON-"].update(disabled=False)
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break

        elif event == "-REFRESH-JOYSTICKS-BUTTON-":
            update_joysticks()

        elif event == "-GAMEPAD-LIST-":
            clicked_string = values["-GAMEPAD-LIST-"][0]
            if clicked_string != "":
                selected_joystick = int(clicked_string.split(".")[0])

        elif event == "-START-TEST-BUTTON-":
            if len(joysticks) == 0:
                error_popup("No Gamepads Found")
                continue

            window["-START-TEST-BUTTON-"].update(disabled=True)

            samples = get_sample_count()
            stick = get_stick()

            reset_progress_bar()
            toggle_progress_bar(True)
            window.refresh()

            result = test_execution(
                samples=samples,
                stick=stick,
                joystick=joysticks[selected_joystick],
                tick=update_progress_bar,
            )

            toggle_progress_bar(False)

            update_result_table(data=result)

            data = wrap_data_for_server(result=result)

            window["-UPLOAD-BUTTON-"].update(disabled=False)
            window["-SAVE-BUTTON-"].update(disabled=False)

        elif event == "-UPLOAD-BUTTON-":
            upload_popup(data=data)

        elif event == "-SAVE-BUTTON-":
            write_to_file(data=data, path=values["-SAVE-BUTTON-"])

        elif event == "-SHOW-LICENSES-BUTTON-":
            license_popup()

    window.close()


if __name__ == "__main__":
    app()
