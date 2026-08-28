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


class FilteringResult(TypedDict):
    timings_filtered: list[float]
    outliers_upper: list[float]
    outliers_lower: list[float]


def filter_outliers(timings: list[float]) -> FilteringResult:
    """
    Function to filter out outliers in latency data.
    """

    timings_sorted = sorted(timings)

    q1 = np.quantile(timings_sorted, 0.25)
    q3 = np.quantile(timings_sorted, 0.75)
    range = q3 - q1
    lower_bound = q1 - 1.5 * range
    upper_bound = q3 + 1.5 * range

    return FilteringResult(
        timings_filtered=[
            delta for delta in timings if lower_bound <= delta <= upper_bound
        ],
        outliers_upper=[delta for delta in timings if upper_bound < delta],
        outliers_lower=[delta for delta in timings if delta < lower_bound],
    )


class TestResults(TypedDict):
    os_name: str
    joystick_name: str
    polling_rate: float
    timings: list[float]
    timings_filtered_avg: float
    timings_filtered_min: float
    timings_filtered_max: float
    jitter: float
    outlier_lower_ratio: float
    outlier_lower_avg: float
    outlier_upper_ratio: float
    outlier_upper_avg: float


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

    filter_result = filter_outliers(timings)

    timings_filtered_avg = np.mean(filter_result["timings_filtered"])
    polling_rate = 1000 / timings_filtered_avg

    return TestResults(
        os_name=platform.system(),
        joystick_name=pygame_joystick.get_name(),
        polling_rate=float(polling_rate),
        timings=timings,
        timings_filtered_avg=float(timings_filtered_avg),
        timings_filtered_min=min(filter_result["timings_filtered"]),
        timings_filtered_max=max(filter_result["timings_filtered"]),
        jitter=float(np.std(filter_result["timings_filtered"])),
        outlier_lower_avg=float(np.mean(filter_result["outliers_lower"])),
        outlier_lower_ratio=float(len(filter_result["outliers_lower"]) / sample_count),
        outlier_upper_avg=float(np.mean(filter_result["outliers_upper"])),
        outlier_upper_ratio=float(len(filter_result["outliers_upper"]) / sample_count),
    )


class GamepadlaUploadData(TypedDict):
    test_key: str
    version: str
    url: str
    date: str
    driver: str
    os_name: str
    os_version: str
    min_latency: float
    avg_latency: float
    max_latency: float
    polling_rate: float
    jitter: float
    mathod: str
    delay_list: str
    connection: str
    name: str


def wrap_data_for_server(result: TestResults) -> GamepadlaUploadData:
    """
    Wraps the test result struct into another struct for compatibility.
    """
    stamp = uuid.uuid4()
    uname = platform.uname()
    os_version = uname.version

    return GamepadlaUploadData(
        test_key=str(stamp),
        version=f"gamepadla-plus@{__version__}",
        url="https://gamepadla.com",
        date=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        driver=result["joystick_name"],
        os_name=result["os_name"],
        os_version=os_version,
        min_latency=round(result["timings_filtered_min"], 2),
        avg_latency=round(result["timings_filtered_avg"], 2),
        max_latency=round(result["timings_filtered_max"], 2),
        polling_rate=round(result["polling_rate"], 2),
        jitter=round(result["jitter"], 2),
        mathod="GP",
        delay_list=", ".join([f"{x:.2f}" for x in result["timings"]]),
        connection="",
        name="",
    )


def upload_data(
    data: GamepadlaUploadData, connection: GamePadConnection, name: str
) -> bool:
    """
    Uploads results to server.
    """
    # Add connection and gamepad name to the data
    data["connection"] = connection.value
    data["name"] = name

    # Send test results to the server
    response = requests.post("https://gamepadla.com/scripts/poster.php", data=data)

    return response.status_code == 200


def write_to_file(data: GamepadlaUploadData, path: str):
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
