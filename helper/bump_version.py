import re
import sys
from datetime import datetime
from pathlib import Path

from gamepadla_plus.__about__ import __version__

USAGE = "Usage: task version:bump -- X.Y.Z"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
UNRELEASED = "## Unreleased"


def bump_file(file: Path, old_version: str, new_version: str) -> int:
    content = file.read_text(encoding="utf-8")
    count = content.count(old_version)
    if count == 0:
        print(f"ERROR: no occurrence of {old_version!r} in {file}.", file=sys.stderr)
        raise SystemExit(1)
    file.write_text(content.replace(old_version, new_version), encoding="utf-8")
    print(f"Updated {file}: {count}x {old_version} -> {new_version}")
    return count


def main() -> int:
    if len(sys.argv) != 2 or not SEMVER.fullmatch(sys.argv[1]):
        print(USAGE, file=sys.stderr)
        return 1

    new_version = sys.argv[1]
    old_version = __version__

    if old_version == new_version:
        print(f"Version is already {new_version}.", file=sys.stderr)
        return 1

    for file in [
        Path("gamepadla_plus/__about__.py"),
        Path("snapcraft.yaml"),
        Path("README.md"),
    ]:
        bump_file(file, old_version, new_version)

    changelog = Path("CHANGELOG.md")
    content = changelog.read_text(encoding="utf-8")
    if UNRELEASED in content:
        date = datetime.now().astimezone().date().isoformat()
        changelog.write_text(
            content.replace(UNRELEASED, f"## v{new_version} -- {date}", 1),
            encoding="utf-8",
        )
        print(f"Updated {changelog}: '{UNRELEASED}' -> '## v{new_version} -- {date}'")
    else:
        print(f"WARNING: no '{UNRELEASED}' heading in {changelog}, left unchanged.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
