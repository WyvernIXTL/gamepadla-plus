<div align="center">

# `gamepadla-plus`

**Gamepad polling rate and synthetic latency tester. (CLI and GUI)**

[![PyPI - Version](https://img.shields.io/pypi/v/gamepadla-plus)](https://pypi.org/project/gamepadla-plus/)
[![GitHub License](https://img.shields.io/github/license/WyvernIXTL/gamepadla-plus)](https://github.com/WyvernIXTL/gamepadla-plus/blob/main/LICENSE)

</div>

Gamepadla is an easy way to check the polling rate of your gamepad. This tool will help you get accurate data about your controller's performance, which can be useful for gamers, game developers, and enthusiasts.  
Gamepadla works with most popular gamepads and supports DInput and XInput protocols, making it a versatile solution for testing different types of controllers.  

*Gamepadla+ or gamepadla-plus is a hard fork of [Gamepadla](https://github.com/cakama3a/Polling/tree/71a53424d4faad0edc90577c149f543696a4b947).*

![GUI Demo](./img/gamepadla-plus-gui-demo.gif)

[![asciicast](https://asciinema.org/a/686853.svg)](https://asciinema.org/a/686853)


## Installation

### [`uv`](https://github.com/astral-sh/uv)

```
uv tool install gamepadla-plus
```

### [`pipx`](https://github.com/pypa/pipx)

```
pipx install gamepadla-plus
```

### `pip`

```
pip install gamepadla-plus
```


## Usage (GUI)

1. Execute the program `gamepadla` without any arguments.
2. If you haven't connected any controller do it now and click `Refresh`.
3. Click `Test` and rotate the stick you chose slowly at the edge.
4. Optionally save the result to a JSON file or upload the result to <gamepadla.com>.


## Usage (CLI)

```
# gamepadla.exe --help

 Usage: gamepadla [OPTIONS] COMMAND [ARGS]...

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
gamepadla list
```
```
# gamepadla list
Found 1 controllers
0. Xbox 360 Controller
```

2. Test the controller with the id from step one (`test` defaults to id 0):
```
gamepadla test 0
```
equals here
```
gamepadla test
```
```
# gamepadla test
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
gamepadla test --stick right
```

#### Write Result to JSON File

```
gamepadla test --out data.json
```

### Upload Result to <gamepadla.com>

```
gamepadla test --upload
```


## Disclaimer

Gamepadla measures the delay between successive changes in the position of the analog stick on the gamepad, rather than the traditional input latency, which measures the time between pressing a button on the gamepad and a response in a program or game.  
This method of measurement can be affected by various factors, including the quality of the gamepad, the speed of the computer's processor, the speed of event processing in the Pygame library, and so on.  
Therefore, although Gamepadla can give a general idea of the "response" of a gamepad, it cannot accurately measure input latency in the traditional sense. The results obtained from Gamepadla should be used as a guide, not as an exact measurement of input latency.


## Contributors

* [John Punch](https://www.reddit.com/user/JohnnyPunch/)
* [Adam McKellar](https://github.com/WyvernIXTL)


## Notable Mentions

Based on the method of Christian P.: <https://github.com/chrizonix/XInputTest>.


## License

Licensed under MIT.


## Contributing

Please have a look at [`CONTRIBUTING.md`](./CONTRIBUTING.md).


## Why this is a Hard Fork

* `cakama3a/Polling` (formerly known as `Gamepadla`) has 200MB git history. 
  Sadly many build artifacts and release binaries are in said git history. 
  Cloning that repo is not fun. And removing those directories from my history essentialy made my repo a hard fork.
* `cakama3a` (aka John Punch) is very unresponsive regarding the addition of pip support for the software. A simple `pyproject.toml` was sitting ducks in the PR while he still happily adds more release artifacts to the git history.
* I made major additions like the GUI and the CLI to my fork.

