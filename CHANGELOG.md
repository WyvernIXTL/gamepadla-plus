# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

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

- Wrong file type in save dialog.
