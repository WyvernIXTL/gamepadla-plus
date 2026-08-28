import webbrowser

import FreeSimpleGUI as sg
import pygame
from pygame.joystick import JoystickType
from rich.traceback import install as traceback_install

from gamepadla_plus.__init__ import LICENSE_FILE_NAME, THIRD_PARTY_LICENSE_FILE_NAME
from gamepadla_plus.common import (
    GamePadConnection,
    GamepadlaError,
    GamepadlaUploadData,
    StickSelector,
    TestResults,
    get_joysticks,
    read_license,
    test_execution,
    upload_data,
    wrap_data_for_server,
    write_to_file,
)
from gamepadla_plus.icon import ICON


class GuiError(Exception):
    """Exception raised for fatal GUI error."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def error_popup(msg: str):
    sg.Window("Error", [[sg.Text(msg)], [sg.Push(), sg.Button("Continue")]]).read(
        close=True
    )


def third_party_license_popup(licenses: str):
    sg.Window(
        "3rd Party Licenses",
        [
            [sg.Multiline(licenses, size=(100, 50), wrap_lines=True)],
            [sg.Push(), sg.Button("Continue")],
        ],
    ).read(close=True)


def license_popup():
    third_party_license = read_license(THIRD_PARTY_LICENSE_FILE_NAME)
    event, _ = sg.Window(
        "License",
        [
            [sg.Text(read_license(LICENSE_FILE_NAME))],
            [
                sg.Push(),
                sg.Button(
                    "Third Party Licenses",
                    visible=(third_party_license != ""),
                    key="-THIRD-PARTY-LICENSES-BUTTON-",
                ),
                sg.Push(),
            ],
            [sg.Push(), sg.Button("Continue")],
        ],
    ).read(close=True)

    if event == "-THIRD-PARTY-LICENSES-BUTTON-":
        third_party_license_popup(third_party_license)


def upload_popup(data: GamepadlaUploadData):
    window = sg.Window(
        "Upload Results",
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
            raise GamepadlaError("No valid connection chosen.")

    while True:
        event, _values = window.read()

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
    data: GamepadlaUploadData | None = None
    count = 0

    layout = [
        [
            sg.Push(),
            sg.Button(
                "Licenses",
                key="-SHOW-LICENSES-BUTTON-",
                disabled=(read_license(LICENSE_FILE_NAME) == ""),
            ),
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
                sg.Radio("4000", group_id=1, default=False, key="-SAMPLE-RADIO-4000-"),
                sg.Radio("8000", group_id=1, default=False, key="-SAMPLE-RADIO-8000-"),
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
                num_rows=13,
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

    window = sg.Window("Gamepadla+", layout, finalize=True, size=(400, 600), icon=ICON)

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
        if window["-SAMPLE-RADIO-4000-"].get():
            return 4000
        if window["-SAMPLE-RADIO-8000-"].get():
            return 8000

        raise GuiError("sample selection radio read out")

    def get_stick() -> StickSelector:
        if window["-STICK-RADIO-LEFT-"].get():
            return StickSelector.LEFT
        if window["-STICK-RADIO-RIGHT-"].get():
            return StickSelector.RIGHT

        raise GuiError("stick selection radio read out")

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
            4000: 3,
            8000: 1.5,
        }
        window["-PROGRESS-BAR-"].update(current_count=(count * factor[samples]))
        window["-DELAY-OUTPUT-"].update(f"{delay:05.2f} ms")

    def update_result_table(data: TestResults):
        window["-RESULT-TABLE-"].update(
            [
                ["Gamepad mode", data["joystick_name"]],
                ["Operating System", data["os_name"]],
                ["Polling Rate Avg.", f"{data['polling_rate']:.3f} Hz"],
                ["", ""],
                ["Average latency", f"{data['timings_filtered_avg']:.3f} ms"],
                ["Minimal latency", f"{data['timings_filtered_min']:.3f} ms"],
                ["Maximum latency", f"{data['timings_filtered_max']:.3f} ms"],
                ["Jitter", f"{data['jitter']:.3f} ms"],
                ["", ""],
                [
                    "Outlier lower Avg.",
                    f"{result['outlier_lower_avg']:.3f} ms"
                    if result["outlier_lower_avg"] is not None
                    else "no outliers",
                ],
                ["Outlier lower %", f"{result['outlier_lower_ratio'] * 100:.3f} %"],
                [
                    "Outlier upper Avg.",
                    f"{result['outlier_upper_avg']:.3f} ms"
                    if result["outlier_upper_avg"] is not None
                    else "no outliers",
                ],
                ["Outlier upper %", f"{result['outlier_upper_ratio'] * 100:.3f} %"],
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
            if len(values["-GAMEPAD-LIST-"]) > 0:
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
                sample_count=samples,
                stick_selected=stick,
                pygame_joystick=joysticks[selected_joystick],
                tick=update_progress_bar,
            )

            toggle_progress_bar(False)

            update_result_table(data=result)

            data = wrap_data_for_server(result=result)

            window["-UPLOAD-BUTTON-"].update(disabled=False)
            window["-SAVE-BUTTON-"].update(disabled=False)

        elif event == "-UPLOAD-BUTTON-" and data is not None:
            upload_popup(data=data)

        elif event == "-SAVE-BUTTON-" and data is not None:
            write_to_file(data=data, path=values["-SAVE-BUTTON-"])

        elif event == "-SHOW-LICENSES-BUTTON-":
            license_popup()

    window.close()
