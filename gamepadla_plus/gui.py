import webbrowser
import pygame
from pygame.joystick import JoystickType
from rich.traceback import install as traceback_install
import FreeSimpleGUI as sg
from sys import platform

from gamepadla_plus.__init__ import LICENSE_FILE_NAME, THIRD_PARTY_LICENSE_FILE_NAME
from gamepadla_plus.common import (
    get_joysticks,
    StickSelector,
    GamePadConnection,
    GamepadlaError,
    write_to_file,
    upload_data,
    test_execution,
    wrap_data_for_server,
    read_license,
)

from gamepadla_plus.icon import ICON


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


def upload_popup(data: dict):
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
            raise GamepadlaError("No valid connection choosen.")

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

    window = sg.Window("Gamepadla+", layout, finalize=True, size=(400, 560), icon=ICON)

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
