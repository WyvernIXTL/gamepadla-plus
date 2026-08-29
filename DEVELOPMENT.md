# Contributing

## Dev Environment

Please use [`uv`](https://docs.astral.sh/uv/) to initialize the virtual environment.

```
uv sync -p 3.11
```

## Code Formatting and Linting

Code should be formatted by [`ruff`](https://docs.astral.sh/ruff/) and linted by [`ty`](https://docs.astral.sh/ty/)

I recommend using [Zed](https://zed.dev/) as it ships with support for both out of the box.


## Version

Versions can be bumped via `hatch version`.

## Creating Demos / Previews

### GUI

```sh
mkdir frames
ffmpeg -f gdigrab -framerate 8 -i title="Gamepadla+" -vf fps=8 frames/frame_%06d.png
cd frames
magick -delay 12.5 -loop 0 -quality 75 frame_*.png gamepadla-plus-gui-demo-v1.8.0.webp
```
