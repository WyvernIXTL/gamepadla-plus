import webbrowser

import darkdetect
import FreeSimpleGUIQt as sg
import pygame
from pygame.joystick import JoystickType
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QHeaderView
from rich.traceback import install as traceback_install

from gamepadla_plus.__init__ import LICENSE_FILE_NAME, THIRD_PARTY_LICENSE_FILE_NAME
from gamepadla_plus.cli import markdown_str_from_result
from gamepadla_plus.common import (
    GamePadConnection,
    GamepadlaError,
    GamepadlaUploadData,
    StickSelector,
    TestResults,
    get_joysticks,
    jitter_rating,
    read_license,
    test_execution,
    upload_data,
    wrap_data_for_server,
    write_to_file,
)
from gamepadla_plus.icon import ICON

TEST_INSTRUCTION = "Please rotate the stick of your gamepad fast in a circle."

# FreeSimpleGUIQt only styles text/background of QRadioButton, the indicator
# (circle + dot) would fall back to a barely visible native rendering.
DARK_RADIO_STYLESHEET = """
QRadioButton::indicator {
    width: 13px;
    height: 13px;
    border: 1px solid #8b9fde;
    border-radius: 7px;
    background-color: #1c1e23;
}
QRadioButton::indicator:checked {
    background-color: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 white, stop:0.45 white, stop:0.55 #1c1e23, stop:1 #1c1e23);
}
QRadioButton::indicator:hover {
    background-color: #313641;
}
"""
LIGHT_RADIO_STYLESHEET = """
QRadioButton::indicator {
    width: 13px;
    height: 13px;
    border: 1px solid #063289;
    border-radius: 7px;
    background-color: #f9f8f4;
}
QRadioButton::indicator:checked {
    background-color: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 black, stop:0.45 black, stop:0.55 #f9f8f4, stop:1 #f9f8f4);
}
QRadioButton::indicator:hover {
    background-color: #e5dece;
}
"""


class GuiError(Exception):
    """Exception raised for fatal GUI error."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def pad_button(window, key, fit_window=False):
    button = window[key]
    button.set_stylesheet(
        button.get_stylesheet() + " QPushButton { padding: 0px 12px; }"
    )
    layout = window.QTWindow.layout()
    layout.invalidate()
    if fit_window:
        window.QT_QMainWindow.adjustSize()
    layout.activate()


def fit_window_to_content(window, width):
    qt_main_window = window.QT_QMainWindow
    hint = qt_main_window.sizeHint()
    qt_main_window.setMinimumSize(width, hint.height())
    qt_main_window.resize(width, hint.height())


def error_popup(msg: str):
    window = sg.Window(
        "Error",
        [[sg.Text(msg)], [sg.Stretch(), sg.Button("Continue")]],
        finalize=True,
    )
    pad_button(window, "Continue", fit_window=True)
    window.read(close=True)


def third_party_license_popup(licenses: str):
    window = sg.Window(
        "3rd Party Licenses",
        [
            [sg.Multiline(licenses, size_px=(560, 400))],
            [sg.Stretch(), sg.Button("Continue")],
        ],
        finalize=True,
    )
    pad_button(window, "Continue", fit_window=True)
    window.read(close=True)


def license_popup():
    third_party_license = read_license(THIRD_PARTY_LICENSE_FILE_NAME)
    window = sg.Window(
        "License",
        [
            [sg.Text(read_license(LICENSE_FILE_NAME))],
            [
                sg.Stretch(),
                sg.Button(
                    "Third Party Licenses",
                    visible=(third_party_license != ""),
                    key="-THIRD-PARTY-LICENSES-BUTTON-",
                ),
                sg.Stretch(),
            ],
            [sg.Stretch(), sg.Button("Continue")],
        ],
        finalize=True,
    )
    pad_button(window, "-THIRD-PARTY-LICENSES-BUTTON-", fit_window=True)
    pad_button(window, "Continue", fit_window=True)
    event, _ = window.read(close=True)

    if event == "-THIRD-PARTY-LICENSES-BUTTON-":
        third_party_license_popup(third_party_license)


def upload_popup(data: GamepadlaUploadData):
    window = sg.Window(
        "Upload Results (Legacy)",
        [
            [
                sg.Text(
                    "Note: This versions upload functionality to gamepadla.com is compatible with Polling v1.3.1.4. "
                    "gamepadla.com generates the result page, but may not count it as a submission."
                )
            ],
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
            [sg.Stretch(), sg.Button("Cancel"), sg.Button("Upload")],
        ],
        finalize=True,
    )

    def get_connection_type(values) -> GamePadConnection:
        if values["-RADIO-CONNECTION-DONGLE-"]:
            return GamePadConnection.DONGLE
        elif values["-RADIO-CONNECTION-CABLE-"]:
            return GamePadConnection.CABLE
        elif values["-RADIO-CONNECTION-BLUETOOTH-"]:
            return GamePadConnection.BLUETOOTH
        else:
            raise GamepadlaError("No valid connection chosen.")

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == "Cancel":
            break

        elif event == "Upload":
            connection_type = get_connection_type(values)
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


def check_dark_mode_enabled() -> bool:
    try:
        is_dark_maybe: bool | None = darkdetect.isDark()
        if is_dark_maybe is not None:
            return is_dark_maybe
        else:
            return True
    except Exception:  # noqa: BLE001
        return True


def gui():
    traceback_install()
    pygame.init()
    joysticks: list[JoystickType] = []
    selected_joystick = 0
    result: TestResults | None = None
    data: GamepadlaUploadData | None = None
    count = 0

    dark_mode_is_enabled = check_dark_mode_enabled()

    # https://freesimplegui.readthedocs.io/en/latest/#themes-automatic-coloring-of-your-windows
    # sg.theme_previewer()

    if dark_mode_is_enabled:
        sg.theme("DarkGrey12")
    else:
        sg.theme("TanBlue")

    layout = [
        [
            sg.Stretch(),
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
                select_mode="single",
                size_px=(None, 140),
            ),
        ],
        [
            sg.Button(
                "Refresh",
                key="-REFRESH-JOYSTICKS-BUTTON-",
            ),
        ],
        [
            sg.Text("Samples:"),
            sg.Stretch(),
            sg.Radio("2000", group_id=1, default=True, key="-SAMPLE-RADIO-2000-"),
            sg.Radio("4000", group_id=1, default=False, key="-SAMPLE-RADIO-4000-"),
            sg.Radio("8000", group_id=1, default=False, key="-SAMPLE-RADIO-8000-"),
            sg.Radio("16000", group_id=1, default=False, key="-SAMPLE-RADIO-16000-"),
        ],
        [
            sg.Text("Stick:"),
            sg.Stretch(),
            sg.Radio("left", group_id=2, default=True, key="-STICK-RADIO-LEFT-"),
            sg.Radio(
                "right",
                group_id=2,
                default=False,
                key="-STICK-RADIO-RIGHT-",
            ),
        ],
        [
            sg.Button("Test", key="-START-TEST-BUTTON-"),
        ],
        [
            sg.Text(
                "",
                key="-TEST-INSTRUCTION-",
            ),
        ],
        [
            sg.ProgressBar(
                12000,
                key="-PROGRESS-BAR-",
                size_px=(300, 3),
                bar_color=("red", "grey") if dark_mode_is_enabled else ("red", "white"),
            ),
            sg.Text("", key="-DELAY-OUTPUT-"),
        ],
        [
            sg.Table(
                [["", ""]],
                headings=["Parameter", "Value"],
                key="-RESULT-TABLE-",
                def_col_width=20,
                auto_size_columns=False,
                max_col_width=100,
                num_rows=14,
                justification="left",
                text_color=None if dark_mode_is_enabled else "black",
            )
        ],
        [
            sg.Button(
                "Upload Result (Legacy)",
                disabled=True,
                key="-UPLOAD-BUTTON-",
            ),
        ],
        [
            sg.FileSaveAs(
                "Save to File",
                disabled=True,
                key="-SAVE-BUTTON-",
                file_types=(("JSON", "*.json"),),
                enable_events=True,
            ),
        ],
        [
            sg.Button(
                "Copy as Markdown",
                disabled=True,
                key="-COPY-MARKDOWN-BUTTON-",
            ),
        ],
    ]

    window = sg.Window(
        "Gamepadla+",
        layout,
        finalize=True,
        size=(400, 820),
        icon=ICON,
    )
    qt_application = window.QTApplication
    assert qt_application is not None
    qt_application.setStyleSheet(
        DARK_RADIO_STYLESHEET if dark_mode_is_enabled else LIGHT_RADIO_STYLESHEET
    )
    result_table_element = window["-RESULT-TABLE-"]
    result_table = result_table_element.QT_TableWidget
    result_table.verticalHeader().setVisible(False)
    result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    result_table.setFixedHeight(
        result_table.horizontalHeader().height()
        + result_table_element.NumRows
        * result_table.verticalHeader().defaultSectionSize()
        + 2 * result_table.frameWidth()
    )
    progress_bar_widget = window["-PROGRESS-BAR-"].Widget
    progress_bar_stylesheet = progress_bar_widget.styleSheet()
    hidden_progress_bar_stylesheet = (
        "QProgressBar { background: transparent; border: none; }"
        " QProgressBar::chunk { background: transparent; }"
    )
    progress_bar_widget.setStyleSheet(hidden_progress_bar_stylesheet)
    pad_button(window, "-SHOW-LICENSES-BUTTON-")
    fit_window_to_content(window, 400)

    def update_joysticks():
        nonlocal joysticks, selected_joystick
        if new_joysticks := get_joysticks():
            joysticks = new_joysticks
            joystick_names = [
                f"{i}. {j.get_name()}" for (i, j) in enumerate(new_joysticks)
            ]
            window["-GAMEPAD-LIST-"].update(joystick_names)
        else:
            joysticks = []
            window["-GAMEPAD-LIST-"].update([])

        if selected_joystick >= len(joysticks):
            selected_joystick = 0

    update_joysticks()

    def get_sample_count(values) -> int:
        if values["-SAMPLE-RADIO-2000-"]:
            return 2000
        if values["-SAMPLE-RADIO-4000-"]:
            return 4000
        if values["-SAMPLE-RADIO-8000-"]:
            return 8000
        if values["-SAMPLE-RADIO-16000-"]:
            return 16000

        raise GuiError("sample selection radio read out")

    def get_stick(values) -> StickSelector:
        if values["-STICK-RADIO-LEFT-"]:
            return StickSelector.LEFT
        if values["-STICK-RADIO-RIGHT-"]:
            return StickSelector.RIGHT

        raise GuiError("stick selection radio read out")

    def toggle_progress_bar(on: bool):
        if on:
            progress_bar_widget.setStyleSheet(progress_bar_stylesheet)
            window["-TEST-INSTRUCTION-"].update(TEST_INSTRUCTION)
        else:
            progress_bar_widget.setStyleSheet(hidden_progress_bar_stylesheet)
            window["-TEST-INSTRUCTION-"].update("")
            window["-PROGRESS-BAR-"].update_bar(current_count=0)
            window["-DELAY-OUTPUT-"].update("")

    def reset_progress_bar():
        nonlocal count
        window["-PROGRESS-BAR-"].update_bar(current_count=0)
        window["-DELAY-OUTPUT-"].update("")
        count = 0

    def update_progress_bar(delay: float):
        nonlocal count
        count += 1
        factor = 12000 / samples
        window["-PROGRESS-BAR-"].update_bar(current_count=(count * factor))
        window["-DELAY-OUTPUT-"].update(f"{delay:05.2f} ms")

    def update_result_table(result: TestResults):
        window["-RESULT-TABLE-"].update(
            [
                ["Gamepad Name", result["gamepad_name"]],
                ["Operating System", result["os_name"]],
                ["Polling Rate (p10)", f"{result['polling_rate']:.3f} Hz"],
                ["", ""],
                ["Average latency", f"{result['timings_filtered_avg']:.3f} ms"],
                ["Minimal latency", f"{result['timings_filtered_min']:.3f} ms"],
                ["Maximum latency", f"{result['timings_filtered_max']:.3f} ms"],
                [
                    "Jitter (CV)",
                    f"{result['jitter_pct']:.2f} % ({jitter_rating(result['jitter_pct'])}), {result['jitter']:.3f} ms",
                ],
                ["Missed Reports", f"{result['missed_report_ratio'] * 100:.2f} %"],
                ["", ""],
                [
                    "Outlier lower Avg. (IQR)",
                    f"{result['outlier_lower_avg']:.3f} ms"
                    if result["outlier_lower_avg"] is not None
                    else "no outliers",
                ],
                [
                    "Outlier lower % (IQR)",
                    f"{result['outlier_lower_ratio'] * 100:.3f} %",
                ],
                [
                    "Outlier upper Avg. (IQR)",
                    f"{result['outlier_upper_avg']:.3f} ms"
                    if result["outlier_upper_avg"] is not None
                    else "no outliers",
                ],
                [
                    "Outlier upper % (IQR)",
                    f"{result['outlier_upper_ratio'] * 100:.3f} %",
                ],
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

            samples = get_sample_count(values)
            stick = get_stick(values)

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

            update_result_table(result=result)

            data = wrap_data_for_server(result=result)

            window["-UPLOAD-BUTTON-"].update(disabled=False)
            window["-SAVE-BUTTON-"].update(disabled=False)
            window["-COPY-MARKDOWN-BUTTON-"].update(disabled=False)

        elif event == "-UPLOAD-BUTTON-" and data is not None:
            upload_popup(data=data)

        elif event == "-SAVE-BUTTON-" and result is not None:
            save_path = values["-SAVE-BUTTON-"]
            if isinstance(save_path, tuple):
                save_path = save_path[0]
            if save_path:
                write_to_file(result=result, path=save_path)

        elif event == "-COPY-MARKDOWN-BUTTON-" and result is not None:
            result_md = markdown_str_from_result(result)
            QGuiApplication.clipboard().setText(str(result_md))

        elif event == "-SHOW-LICENSES-BUTTON-":
            license_popup()

    window.close()
