import json
import os
import platform
import sys
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

    # To detect new gamepads on all platforms, the joystick module needs to be reinitialized.
    pygame.event.pump()
    pygame.joystick.quit()
    pygame.joystick.init()

    joysticks = [
        pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())
    ]

    if joysticks:
        return joysticks
    else:
        return None


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


def jitter_rating(jitter_pct: float) -> str:
    if jitter_pct < 2:
        return "excellent"
    if jitter_pct < 10:
        return "normal"
    return "sloppy"


class TestResults(TypedDict):
    os_name: str
    joystick_name: str
    polling_rate: float
    polling_rate_avg: float
    timings: list[float]
    timings_filtered_avg: float
    timings_filtered_min: float
    timings_filtered_max: float
    jitter: float
    jitter_pct: float
    missed_report_ratio: float
    outlier_lower_ratio: float
    outlier_lower_avg: float | None
    outlier_upper_ratio: float
    outlier_upper_avg: float | None


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

    STICK_ENGAGE_THRESHOLD = 0.1

    # initialize values
    while True:
        pygame.event.pump()
        x = pygame_joystick.get_axis(axis_x)
        y = pygame_joystick.get_axis(axis_y)
        pygame.event.clear()

        if not (abs(x) < STICK_ENGAGE_THRESHOLD and abs(y) < STICK_ENGAGE_THRESHOLD):
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
        if not (abs(x) < STICK_ENGAGE_THRESHOLD and abs(y) < STICK_ENGAGE_THRESHOLD) and (x != x_old or y != y_old):
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
    period_estimate = float(np.percentile(filter_result["timings_filtered"], 10))
    polling_rate = 1000 / period_estimate

    on_time = [
        d
        for d in filter_result["timings_filtered"]
        if 0.5 * period_estimate <= d <= 1.5 * period_estimate
    ]
    if not on_time:
        on_time = filter_result["timings_filtered"]

    on_time_avg = float(np.mean(on_time))
    jitter_pct = float(np.std(on_time)) / on_time_avg * 100
    missed_report_ratio = float(
        len([d for d in timings if d > 1.5 * period_estimate]) / sample_count
    )
    polling_rate_avg = 1000 / timings_filtered_avg

    return TestResults(
        os_name=platform.system(),
        joystick_name=pygame_joystick.get_name(),
        polling_rate=float(polling_rate),
        polling_rate_avg=float(polling_rate_avg),
        timings=timings,
        timings_filtered_avg=float(timings_filtered_avg),
        timings_filtered_min=min(filter_result["timings_filtered"]),
        timings_filtered_max=max(filter_result["timings_filtered"]),
        jitter=float(np.std(filter_result["timings_filtered"])),
        jitter_pct=jitter_pct,
        missed_report_ratio=missed_report_ratio,
        outlier_lower_avg=float(np.mean(filter_result["outliers_lower"]))
        if len(filter_result["outliers_lower"]) > 0
        else None,
        outlier_lower_ratio=float(len(filter_result["outliers_lower"]) / sample_count),
        outlier_upper_avg=float(np.mean(filter_result["outliers_upper"]))
        if len(filter_result["outliers_upper"]) > 0
        else None,
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
    connection: str | None
    name: str | None


def wrap_data_for_server(result: TestResults) -> GamepadlaUploadData:
    """
    Wraps the test result struct into another struct for compatibility.
    """
    stamp = uuid.uuid4()
    uname = platform.uname()
    os_version = uname.version

    # Aimed compatibiliy with Polling v1.3.1.4
    # which I just noticed is outdated, nice.
    # Polling v2 is not open source, so compatibliy won't happen until that is released.
    return GamepadlaUploadData(
        test_key=str(stamp),
        version="1.3.1.4",
        url="https://gamepadla.com",
        date=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        driver=result["joystick_name"],
        os_name=result["os_name"],
        os_version=os_version,
        min_latency=round(result["timings_filtered_min"], 2),
        avg_latency=round(result["timings_filtered_avg"], 2),
        max_latency=round(result["timings_filtered_max"], 2),
        polling_rate=round(result["polling_rate_avg"], 2),
        jitter=round(result["jitter"], 2),
        mathod="GP",
        delay_list=", ".join([f"{x:.2f}" for x in result["timings"]]),
        connection=None,
        name=None,
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


def write_to_file(
    data: GamepadlaUploadData, path: str, result: TestResults | None = None
):
    """
    Writes result to file.
    """
    payload = dict(data)
    if result is not None:
        payload["polling_rate_p10"] = round(result["polling_rate"], 2)
        payload["polling_rate_avg"] = round(result["polling_rate_avg"], 2)
        payload["jitter_pct"] = round(result["jitter_pct"], 2)
        payload["missed_report_ratio"] = round(result["missed_report_ratio"], 4)
    with open(path, "w") as outfile:
        json.dump(payload, outfile, indent=4)


def project_root_path() -> str:
    src_path = os.path.dirname(os.path.realpath(__file__))
    root_path = os.path.abspath(os.path.join(src_path, os.pardir))
    if not os.path.isdir(root_path):
        # Compiled binaries resolve __file__ to a virtual path whose parent
        # directories do not exist on disk. The data files are located next to
        # the binary instead.
        root_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    return root_path + "/"


def read_license(license_file_name: str) -> str:
    license_path = project_root_path() + license_file_name
    if os.path.exists(license_path):
        with open(license_path, "r", errors="ignore") as license_file:
            license_text = license_file.read()
        return license_text
    else:
        return ""
