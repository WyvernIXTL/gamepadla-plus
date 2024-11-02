<div align="center">

# `gamepadla-plus`

**Gamepad polling rate and synthetic latency tester.**

[![PyPI - Version](https://img.shields.io/pypi/v/gamepadla-plus)](https://pypi.org/project/gamepadla-plus/)
[![GitHub License](https://img.shields.io/github/license/WyvernIXTL/gamepadla-plus)](https://github.com/WyvernIXTL/gamepadla-plus/blob/main/LICENSE)

</div>

Gamepadla is an easy way to check the polling rate of your gamepad. This tool will help you get accurate data about your controller's performance, which can be useful for gamers, game developers, and enthusiasts.  
Gamepadla works with most popular gamepads and supports DInput and XInput protocols, making it a versatile solution for testing different types of controllers.  


[![asciicast](https://asciinema.org/a/686853.svg)](https://asciinema.org/a/686853)


## Installation

### [`uvx`](https://github.com/astral-sh/uv)

```
uvx install gamepadla-plus
```

### [`pipx`](https://github.com/pypa/pipx)

```
pipx install gamepadla-plus
```


## Usage

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
