<div align="center">

<img src="https://raw.githubusercontent.com/WyvernIXTL/gamepadla-plus/e17852e16a02d095f564ba0caf6589466f7004e5/icon/gamepadla-plus-icon-round-white.svg" alt="Gamepadla+ Icon"  width="200"/>


# Gamepadla+

**Gamepad Polling Rate and Latency Testing Tool (CLI & GUI)**

[![PyPI - Version](https://img.shields.io/pypi/v/gamepadla-plus)](https://pypi.org/project/gamepadla-plus/)
[![GitHub License](https://img.shields.io/github/license/WyvernIXTL/gamepadla-plus)](https://github.com/WyvernIXTL/gamepadla-plus/blob/main/LICENSE.txt)

</div>

Gamepadla+ is a program for measuring the polling rate and synthetic latency of gamepads aka. controllers.

* Supports DInput and XInput
* Provides CLI *(Command Line Interface)* and GUI *(Graphical User Interface)*
* Shows polling rate and latency metrics


![GUI preview](https://github.com/WyvernIXTL/gamepadla-plus/blob/702007e81a85bc3588da16aa96eca4a383b91dd8/img/gamepadla-plus-gui-demo-v1.9.0.webp)

[![asciicast](https://asciinema.org/a/1264547.svg)](https://asciinema.org/a/1264547)


## Installation

> [!TIP]
> Releases have [*attestation*](https://github.com/WyvernIXTL/gamepadla-plus/attestations/) that they were built in CI.

### Windows

#### Microsoft Store *(Recommended)*

<a href="https://get.microsoft.com/installer/download/9nxr3b5txfph?referrer=appbadge" target="_self" >
	<img src="https://get.microsoft.com/images/en-us%20dark.svg" width="200"/>
</a>

#### Installer

[![Download Windows Installer](https://badgen.net/static/Windows/Download%20Installer/?icon=windows&scale=1.5)](https://github.com/WyvernIXTL/gamepadla-plus/releases/download/v1.9.0/gamepadla-plus-v1.9.0-windows-x64-installer.exe)

#### Portable Builds

See the "Assets" section on the release page:

[![Releases v1.9.0](https://badgen.net/static/github/Releases%20v1.9.0/?icon=github&label&scale=1.5)](https://github.com/WyvernIXTL/gamepadla-plus/releases/download/v1.9.0)


#### From Source

Using [`uv`](https://github.com/astral-sh/uv):
```sh
uv tool install --python 3.11 gamepadla-plus@1.9.0
```

### Linux

#### [Snap](https://snapcraft.io/) *(Recommended)*

If you are no using Ubuntu, Manjaro or Solus you'll likely have to install [`snapd`](https://snapcraft.io/docs/tutorials/install-the-daemon/) first.

```sh
sudo snap install gamepadla-plus
sudo snap connect gamepadla-plus:joystick
```

#### [AppImages](https://appimage.org/) and Portable Builds

See the "Assets" section on the release page:

[![Releases v1.9.0](https://badgen.net/static/github/Releases%20v1.9.0/?icon=github&label&scale=1.5)](https://github.com/WyvernIXTL/gamepadla-plus/releases/download/v1.9.0)


#### From Source

Using [`uv`](https://github.com/astral-sh/uv):
```sh
uv tool install --python 3.11 gamepadla-plus@1.9.0
```

### macOS

> [!WARNING]
> The app has not been tested with macOS.

#### From Source

Using [`uv`](https://github.com/astral-sh/uv):
```sh
uv tool install --python 3.11 gamepadla-plus@1.9.0
```


## Usage (GUI)

1. Execute the program `Gamepadla+` without any arguments.
2. If you haven't connected any controller do it now and click `Refresh`.
3. Click `Test` and rotate the stick you chose fast in a circle.
4. Optionally save the result to a JSON file or upload the result to <gamepadla.com>.


## Usage (CLI)

```
# gamepadla-plus --help

 Usage: gamepadla-plus [OPTIONS] COMMAND [ARGS]...

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
gamepadla-plus list
```
```
# gamepadla-plus list
Found 1 controllers
0. Xbox 360 Controller
```

2. Test the controller with the id from step one (`test` defaults to id 0):
```
gamepadla-plus test 0
```
equals here
```
gamepadla-plus test
```
```
# gamepadla-plus test
100%|████████████████████████████████████████████████████████████ | 00.97 ms


  Parameter                  Value
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Gamepad Name               Xbox 360 Controller
  Operating System           Windows
  Polling Rate (p10)         1051.635 Hz

  Average latency            1.001 ms
  Minimal latency            0.879 ms
  Maximum latency            1.127 ms
  Jitter (CV)                4.31 % (normal), 0.043 ms
  Missed Reports             5.80 %

  Outlier lower Avg. (IQR)   0.657 ms
  Outlier lower % (IQR)      9.600 %
  Outlier upper Avg. (IQR)   1.922 ms
  Outlier upper % (IQR)      10.900 %

```

### Options

#### Test Right Stick

```
gamepadla-plus test --stick right
```

#### Write Result to JSON File

```
gamepadla-plus test --out data.json
```

### Upload Result to <gamepadla.com>

```
gamepadla-plus test --upload
```


## Disclaimer

Gamepadla+ measures the delay between successive changes in the position of the analog stick on the gamepad, rather than the traditional input latency, which measures the time between pressing a button on the gamepad and a response in a program or game.  
This method of measurement can be affected by various factors, including the quality of the gamepad, the speed of the computer's processor, the speed of event processing in the Pygame library, and so on.  
Therefore, although Gamepadla+ can give a general idea of the "response" of a gamepad, it cannot accurately measure input latency in the traditional sense. The results obtained from Gamepadla+ should be used as a guide, not as an exact measurement of input latency.


## Contributors

* *2024-2026* [Adam McKellar](https://github.com/WyvernIXTL)
* *2022-2024* [John Punch](https://github.com/cakama3a) [![John Punch](https://badgen.net/static/icon/John%20Punch?icon=reddit&label&color=orange)](https://www.reddit.com/user/JohnnyPunch/)


## Notable Mentions

Gamepadla+ or gamepadla-plus is a hard fork of [Gamepadla](https://github.com/cakama3a/Polling/tree/71a53424d4faad0edc90577c149f543696a4b947) (known as Polling now).

The testing is based on the method of Christian P.: <https://github.com/chrizonix/XInputTest>.

## Misc.

### Result Upload Functionality to gamepadla.com

The upload functionality to [gamepadla.com](https://gamepadla.com) is compatible with Polling v1.3.1.4.

## License

Licensed under MIT.


## Contributing

Please have a look at [`DEVELOPMENT.md`](./DEVELOPMENT.md).
