import queue
import sys
import threading
import traceback
import webbrowser

import darkdetect
import FreeSimpleGUIQt as sg
import pygame
from pygame.joystick import JoystickType
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWidgets import QApplication, QHeaderView
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

SAMPLE_RADIO_KEYS = (
    "-SAMPLE-RADIO-2000-",
    "-SAMPLE-RADIO-4000-",
    "-SAMPLE-RADIO-8000-",
    "-SAMPLE-RADIO-16000-",
)
STICK_RADIO_KEYS = (
    "-STICK-RADIO-LEFT-",
    "-STICK-RADIO-RIGHT-",
)
OPTION_KEYS = (*SAMPLE_RADIO_KEYS, *STICK_RADIO_KEYS)
CONNECTION_RADIO_KEYS = (
    "-RADIO-CONNECTION-DONGLE-",
    "-RADIO-CONNECTION-CABLE-",
    "-RADIO-CONNECTION-BLUETOOTH-",
)

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


def _parse_color(color: str) -> QColor:
    qt_color = QColor(color)
    if not qt_color.isValid():
        qt_color = QColor("#808080")
    return qt_color


def _shade_color(color: str, factor: float) -> str:
    qt_color = _parse_color(color)
    if factor >= 1:
        qt_color = qt_color.lighter(round(factor * 100))
    else:
        qt_color = qt_color.darker(round(100 / factor))
    return qt_color.name()


def _qss_rgba(color: str, alpha: int) -> str:
    qt_color = _parse_color(color)
    return f"rgba({qt_color.red()},{qt_color.green()},{qt_color.blue()},{alpha})"


def _append_qss(element, qss: str):
    # FreeSimpleGUIQt styles every widget with a stylesheet that has no
    # :hover/:pressed/:disabled rules, which disables Qt's native rendering of
    # those states. Appending to the element's persistent QtStyle (re-applied on
    # every element.update()) keeps the state rules in place across
    # enable/disable toggles.
    style = element.qt_styles[0]
    style.append_css_to_end.append(qss)
    element.Widget.setStyleSheet(style.build_css_string())


def style_button(window, key, pad=False, fit_window=False):
    button = window[key]
    fg, bg = sg.theme_button_color()
    fg = fg if fg else (sg.theme_text_color() or "#000000")
    bg = bg if bg else (sg.theme_background_color() or "#d0d0d0")
    if pad:
        _append_qss(button, " QPushButton { padding: 0px 12px; }")
    _append_qss(
        button,
        f" QPushButton:hover {{ background-color: {_shade_color(bg, 1.15)}; }}"
        f" QPushButton:pressed {{ background-color: {_shade_color(bg, 0.7)}; }}"
        f" QPushButton:disabled {{"
        f" color: {_qss_rgba(fg, 90)};"
        f" background-color: {_qss_rgba(bg, 110)};"
        f" }}",
    )
    if pad:
        layout = window.QTWindow.layout()
        layout.invalidate()
        if fit_window:
            window.QT_QMainWindow.adjustSize()
        layout.activate()


def style_element_disabled(window, key):
    element = window[key]
    widget = element.Widget
    class_name = widget.metaObject().className()
    text_color = sg.theme_text_color() or "#000000"
    _append_qss(
        element,
        f" {class_name}:disabled {{ color: {_qss_rgba(text_color, 110)}; }}",
    )


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
    style_button(window, "Continue", pad=True, fit_window=True)
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
    style_button(window, "Continue", pad=True, fit_window=True)
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
    style_button(window, "-THIRD-PARTY-LICENSES-BUTTON-", pad=True, fit_window=True)
    style_button(window, "Continue", pad=True, fit_window=True)
    event, _ = window.read(close=True)

    if event == "-THIRD-PARTY-LICENSES-BUTTON-":
        third_party_license_popup(third_party_license)


def _upload_worker(
    data: GamepadlaUploadData,
    name: str,
    connection: GamePadConnection,
    result_queue: queue.Queue[bool],
):
    try:
        result_queue.put(upload_data(data=data, name=name, connection=connection))
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        result_queue.put(False)


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

    style_button(window, "Cancel", pad=True)
    style_button(window, "Upload", pad=True, fit_window=True)
    for key in CONNECTION_RADIO_KEYS:
        style_element_disabled(window, key)

    def get_connection_type(values) -> GamePadConnection:
        if values["-RADIO-CONNECTION-DONGLE-"]:
            return GamePadConnection.DONGLE
        elif values["-RADIO-CONNECTION-CABLE-"]:
            return GamePadConnection.CABLE
        elif values["-RADIO-CONNECTION-BLUETOOTH-"]:
            return GamePadConnection.BLUETOOTH
        else:
            raise GamepadlaError("No valid connection chosen.")

    def set_upload_controls(enabled: bool):
        for key in CONNECTION_RADIO_KEYS:
            window[key].update(disabled=not enabled)
        window["-CONTROLLER-NAME-INPUT-"].update(disabled=not enabled)
        window["Cancel"].update(disabled=not enabled)
        window["Upload"].update(
            text="Upload" if enabled else "Uploading...",
            disabled=not enabled,
        )

    upload_queue: queue.Queue[bool] = queue.Queue()
    uploading = False

    while True:
        event, values = window.read(timeout=100)

        if event == sg.WIN_CLOSED:
            break

        elif uploading:
            try:
                success = upload_queue.get_nowait()
            except queue.Empty:
                continue
            uploading = False
            if success:
                stamp = data["test_key"]
                webbrowser.open(f"https://gamepadla.com/result/{stamp}/")
                break
            set_upload_controls(enabled=True)
            error_popup("Failed uploading results.")

        elif event == "Cancel":
            break

        elif event == "Upload":
            connection_type = get_connection_type(values)
            controller_name = window["-CONTROLLER-NAME-INPUT-"].get()
            set_upload_controls(enabled=False)
            uploading = True
            threading.Thread(
                target=_upload_worker,
                args=(data, controller_name, connection_type, upload_queue),
                daemon=True,
            ).start()

    window.close()


def check_dark_mode_enabled() -> bool:
    app = QGuiApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        # FreeSimpleGUIQt reuses this instance instead of creating a second one,
        # which would raise a shiboken singleton RuntimeError.
        sg.Window.QTApplication = app
    assert isinstance(app, QGuiApplication)
    color_scheme = app.styleHints().colorScheme()

    if color_scheme == Qt.ColorScheme.Light:
        return False
    if color_scheme == Qt.ColorScheme.Dark:
        return True
    return bool(darkdetect.isDark())


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

    licenses_button_enabled = read_license(LICENSE_FILE_NAME) != ""

    layout = [
        [
            sg.Stretch(),
            sg.Button(
                "Licenses",
                key="-SHOW-LICENSES-BUTTON-",
                disabled=not licenses_button_enabled,
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
                size_px=(300, 3),dark mode detection
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
    style_button(window, "-SHOW-LICENSES-BUTTON-", pad=True)
    style_button(window, "-REFRESH-JOYSTICKS-BUTTON-")
    style_button(window, "-START-TEST-BUTTON-")
    style_button(window, "-UPLOAD-BUTTON-")
    style_button(window, "-SAVE-BUTTON-")
    style_button(window, "-COPY-MARKDOWN-BUTTON-")
    for key in ("-GAMEPAD-LIST-", *OPTION_KEYS):
        style_element_disabled(window, key)
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

    def set_ui_locked(locked: bool):
        window["-SHOW-LICENSES-BUTTON-"].update(
            disabled=locked or not licenses_button_enabled
        )
        window["-REFRESH-JOYSTICKS-BUTTON-"].update(disabled=locked)
        window["-GAMEPAD-LIST-"].update(disabled=locked)
        for key in OPTION_KEYS:
            window[key].update(disabled=locked)
        window["-START-TEST-BUTTON-"].update(disabled=locked)
        has_result = result is not None
        window["-UPLOAD-BUTTON-"].update(disabled=locked or not has_result)
        window["-SAVE-BUTTON-"].update(disabled=locked or not has_result)
        window["-COPY-MARKDOWN-BUTTON-"].update(disabled=locked or not has_result)

    while True:
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

            samples = get_sample_count(values)
            stick = get_stick(values)

            set_ui_locked(locked=True)

            reset_progress_bar()
            toggle_progress_bar(True)
            window.refresh()

            result = test_execution(
                sample_count=samples,
                stick_selected=stick,
                pygame_joystick=joysticks[selected_joystick],
                tick=update_progress_bar,
            )

            set_ui_locked(locked=False)

            toggle_progress_bar(False)

            update_result_table(result=result)

            data = wrap_data_for_server(result=result)

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
