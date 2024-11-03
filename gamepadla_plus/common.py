from typing import Callable
import os
from enum import Enum
import time
import json
import numpy as np
import platform
import requests
import uuid
import pygame
from pygame.joystick import JoystickType

from .__init__ import __version__, LICENSE_FILE_NAME


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


def read_license() -> str:
    src_path = os.path.dirname(os.path.realpath(__file__))
    license_path = src_path + "/../" + LICENSE_FILE_NAME
    with open(license_path, "r") as license_file:
        license_text = license_file.read()
    return license_text
