from importlib import metadata
from os import environ

try:
    __version__ = metadata.version(__package__)
except:  # noqa: E722
    __version__ = "NONE"

environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

LICENSE_FILE_NAME = "LICENSE.txt"
THIRD_PARTY_LICENSE_FILE_NAME = "THIRD-PARTY-LICENSES.txt"
VERSION = f"gamepadla-plus {__version__}"

del metadata
