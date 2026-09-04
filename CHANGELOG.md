# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Changed

- Moved to `pygame-ce` and subsequently removed max supported python versions.
  Instead, the README documents the supported versions.

## v1.9.0 -- 2026-09-03

### Added

- Automatically switch to white theme if detected.
- Bumped sample selection in GUI.

### Changed

- Improved testing and metrics.
- Switch to Qt backed renderer.
- Changed theme for dark mode.
- Updated result file format to reflect better metrics.
- Marked upload to gamepadla.com as legacy.
- Buttons and radios are visibly disabled during testing.
- GUI remains usable during upload.

### Fixed

- PyPi releases shipping without source files. 😅 Sorry!
- GUI not correctly scaling with the display scale factor.
- Controllers connected after startup not being detected by the refresh button in the GUI on Linux.
- Starting test after unplugging and refreshing gamepads likely crashing the program.


## v1.8.2 -- 2026-08-29

### Fixed

- CI failing to upload artifacts.


## v1.8.1 -- 2026-08-29

### Changed

- Changed the script entry point from `Gamepadla+` to `gamepadla-plus`.

### Fixed

- CI package publishing failing due to name of script entry point. 


## v1.8.0 -- 2026-08-29

### Added

- Copy markdown button in GUI.

### Changed

- Update measuring algorithm to be more accurate.
- Filter outliers more effectively.
- Bumped sample numbers in GUI.
- Improved code quality.
- Renamed script entry point and executable from `gamepadla` to `Gamepadla+`.
- Use Nuitka for compiling app instead of PyInstaller. This means that Gamepadla+ starts faster and should feel smoother.

### Fixed

- Failed execution after installation from source due to `typer v0.12.2` not pinning `click`.
- Wrong file type in save dialog.

### Removed

- Max refresh rate display, as this metric appears to be inaccurate.
