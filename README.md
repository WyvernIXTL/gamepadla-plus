<div align="center">

<img src="https://raw.githubusercontent.com/WyvernIXTL/gamepadla-plus/e17852e16a02d095f564ba0caf6589466f7004e5/icon/gamepadla-plus-icon-round-white.svg" alt="Gamepadla+ Icon"  width="200"/>


# Gamepadla+

**Gamepad Polling Rate and Latency Testing Tool (CLI & GUI)**

[![PyPI - Version](https://img.shields.io/pypi/v/gamepadla-plus)](https://pypi.org/project/gamepadla-plus/)
[![GitHub License](https://img.shields.io/github/license/WyvernIXTL/gamepadla-plus)](https://github.com/WyvernIXTL/gamepadla-plus/blob/main/LICENSE)

</div>

Gamepadla+ is a program for measuring the polling rate and synthetic latency of gamepads aka. controllers.

* Supports DInput and XInput
* Provides CLI and GUI
* Shows polling rate and latency metrics


![GUI preview](https://github.com/WyvernIXTL/gamepadla-plus/blob/cf529db1f42d04e9291f18344ebbfb4677a72f04/img/gamepadla-plus-gui-demo-v1.8.0.webp)

[![asciicast](https://asciinema.org/a/1264153.svg)](https://asciinema.org/a/1264153)


## Installation

### [`uv`](https://github.com/astral-sh/uv) (Windows / Linux / MacOS)

```sh
uv tool install --python 3.11 gamepadla-plus
```

### Prebuilt Binaries (Windows)

<a href="https://github.com/WyvernIXTL/gamepadla-plus/releases/latest/download/gamepadla-plus-windows-x64-installer.exe">
  <img alt="Download for Windows" src="https://img.shields.io/badge/Download-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" height="50">
</a>


## Usage (GUI)

1. Execute the program `Gamepadla+` without any arguments.
2. If you haven't connected any controller do it now and click `Refresh`.
3. Click `Test` and rotate the stick you chose slowly at the edge.
4. Optionally save the result to a JSON file or upload the result to <gamepadla.com>.


## Usage (CLI)

```
# Gamepadla+ --help

 Usage: Gamepadla+ [OPTIONS] COMMAND [ARGS]...

 Gamepad latency and polling rate tester.

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                                            │
│ --show-completion             Show completion for the current shell, to copy it or customize the installation.     │
│ --help                        Show this message and exit.                                                          │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ list   List controller id's.                                                                                       │
│ test   Test controller with id.                                                                                    │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Getting Started

1. List all controllers connected with:
```
Gamepadla+ list
```
```
# Gamepadla+ list
Found 1 controllers
0. Xbox 360 Controller
```

2. Test the controller with the id from step one (`test` defaults to id 0):
```
Gamepadla+ test 0
```
equals here
```
Gamepadla+ test
```
```
# Gamepadla+ test
100%|████████████████████████████████████████████████████████████ | 01.00 ms


  Parameter           Value
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Gamepad mode        Xbox 360 Controller
  Operating System    Windows
  Polling Rate Max.   1000 Hz
  Polling Rate Avg.   964.36 Hz
  Stability           96.44%

  Minimal latency     0.51 ms
  Average latency     1.04 ms
  Maximum latency     2.0 ms
  Jitter              0.16 ms

```

### Options

#### Test Right Stick

```
Gamepadla+ test --stick right
```

#### Write Result to JSON File

```
Gamepadla+ test --out data.json
```

### Upload Result to <gamepadla.com>

```
Gamepadla+ test --upload
```


## Disclaimer

Gamepadla+ measures the delay between successive changes in the position of the analog stick on the gamepad, rather than the traditional input latency, which measures the time between pressing a button on the gamepad and a response in a program or game.  
This method of measurement can be affected by various factors, including the quality of the gamepad, the speed of the computer's processor, the speed of event processing in the Pygame library, and so on.  
Therefore, although Gamepadla+ can give a general idea of the "response" of a gamepad, it cannot accurately measure input latency in the traditional sense. The results obtained from Gamepadla+ should be used as a guide, not as an exact measurement of input latency.


## Contributors

* [John Punch](https://github.com/cakama3a) [![John Punch](https://badgen.net/static/icon/John%20Punch?icon=reddit&label&color=orange)](https://www.reddit.com/user/JohnnyPunch/)
* [Adam McKellar](https://github.com/WyvernIXTL)


## Notable Mentions

Gamepadla+ or gamepadla-plus is a hard fork of [Gamepadla](https://github.com/cakama3a/Polling/tree/71a53424d4faad0edc90577c149f543696a4b947) (known as Polling now).

The testing is based on the method of Christian P.: <https://github.com/chrizonix/XInputTest>.


## License

Licensed under MIT.


## Contributing

Please have a look at [`DEVELOPMENT.md`](./DEVELOPMENT.md).
