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

### CLI

Via `asciinema`:
- Unix: <https://docs.asciinema.org/getting-started/>
- Windows: <https://github.com/Watfaq/PowerSession-rs>


### Trailer

Use [OpenScreen](https://github.com/getopenscreen/openscreen) and export 16/9 1080p for Microsoft Store.

To extract the hero image:

```sh
ffmpeg -sseof -3 -i .\gamepadla-plus-trailer2-v1.8.2.mp4 -q:v 31 -update true gamepadla-plus-heroimage-v1.8.2.png
```

## Other

### Export Icon from SVG to PNG

**Transparent and large:**
```sh
magick -background transparent -density 300 .\icon\gamepadla-plus-icon.svg .\icon\gamepadla-plus-icon_export-transparent.png
oxipng -o max -Z --fast .\icon\gamepadla-plus-icon_export-transparent.png
```

**Linux Desktop:**

```sh
magick -background white -density 600 .\icon\gamepadla-plus-icon.svg -resize 512x512 .\icon\gamepadla-plus-icon_export-solid.png
oxipng -o max -Z --fast .\icon\gamepadla-plus-icon_export-solid.png
```

### Snap Store

- Use the hero image as screenshot.
- Use Vimeo for hosting the demo video.
- Banner:
  ```sh
  magick .\gamepadla-plus-heroimage-v1.9.0.png -gravity north -crop '3:1' +repage .\gamepadla-plus-snap-store-banner-v1.9.0.png
  ```
