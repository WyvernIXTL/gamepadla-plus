import json
import os
import platform
import time
import uuid
from collections.abc import Callable
from enum import Enum
from typing import TypedDict

import numpy as np
import pygame
import requests
from pygame.joystick import JoystickType

from gamepadla_plus.__about__ import __version__


class StickSelector(str, Enum):
    LEFT = "left"
    RIGHT = "right"


class GamePadConnection(str, Enum):
    CABLE = "Cable"
    BLUETOOTH = "Bluetooth"
    DONGLE = "Dongle"


class GamepadlaError(Exception):
    pass


class TestResults(TypedDict):
    os_name: str
    joystick_name: str
    polling_rate: float
    timings: list[float]
    timings_filtered_avg: float
    timings_filtered_min: float
    timings_filtered_max: float
    jitter: float
    outlier_percent: float
    outlier_avg: float


def get_joysticks() -> list[JoystickType] | None:
    """
    Returns a list of gamepads...

    Pygame NEEDS to be initialized first.
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
    sample_count: int,
    stick_selected: StickSelector,
    pygame_joystick: JoystickType,
    tick: Callable[[float], None],
) -> TestResults:
    """
    Executes the testing algorithm.

    Pygame NEEDS to be initialized first.
    """

    pygame_joystick.init()  # Initialize the selected joystick

    match stick_selected:
        case StickSelector.LEFT:
            axis_x = 0  # Axis for the left stick
            axis_y = 1
        case StickSelector.RIGHT:
            axis_x = 2  # Axis for the right stick
            axis_y = 3

    if not pygame_joystick.get_init():
        raise GamepadlaError("Controller not connected")

    timings: list[float] = []
    start: int = 0
    x_old: float = 0.0
    y_old: float = 0.0

    # initialize values
    while True:
        pygame.event.pump()
        x = pygame_joystick.get_axis(axis_x)
        y = pygame_joystick.get_axis(axis_y)
        pygame.event.clear()

        if not ("0.0" in str(x) and "0.0" in str(y)):
            x_old = x
            y_old = y
            start = time.perf_counter_ns()
            break

    # Main loop to gather latency data from joystick movements
    while len(timings) < sample_count:
        pygame.event.pump()
        x = pygame_joystick.get_axis(axis_x)
        y = pygame_joystick.get_axis(axis_y)
        pygame.event.clear()

        # Ensure the stick has moved significantly (anti-drift)
        if not ("0.0" in str(x) and "0.0" in str(y)) and (x != x_old or y != y_old):
            end = time.perf_counter_ns()
            delay = (end - start) / 1_000_000
            start = end
            x_old = x
            y_old = y

            if 0.1 < delay < 150:
                timings.append(delay)
                tick(delay)

    timings_filtered = filter_outliers(timings)

    timings_filtered_avg = np.mean(timings_filtered)
    polling_rate = 1000 / timings_filtered_avg

    # class TestResults(TypedDict):
    #     os_name: str
    #     joystick_name: str
    #     polling_rate: float
    #     timings: list[float]
    #     timings_filtered_avg: float
    #     timings_filtered_min: float
    #     timings_filtered_max: float
    #     jitter: float
    #     outlier_percent: float
    #     outlier_avg: float

    return TestResults(
        os_name=platform.system(),
        joystick_name=pygame_joystick.get_name(),
        polling_rate=float(polling_rate),
        timings=timings,
        timings_filtered_avg=float(timings_filtered_avg),
        timings_filtered_min=min(timings_filtered),
        timings_filtered_max=max(timings_filtered),
        jitter=float(np.std(timings_filtered)),
    )


def wrap_data_for_server(result: dict) -> dict:
    """
    Wraps the test result struct into another struct for compatibility.
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


def project_root_path() -> str:
    src_path = os.path.dirname(os.path.realpath(__file__))
    return src_path + "/../"


def read_license(license_file_name: str) -> str:
    license_path = project_root_path() + license_file_name
    if os.path.exists(license_path):
        with open(license_path, "r", errors="ignore") as license_file:
            license_text = license_file.read()
        return license_text
    else:
        return ""
