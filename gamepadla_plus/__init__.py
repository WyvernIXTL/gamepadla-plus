from importlib import metadata
from os import environ
from gamepadla_plus.__about__ import __version__

environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

LICENSE_FILE_NAME = "LICENSE.txt"
THIRD_PARTY_LICENSE_FILE_NAME = "THIRD-PARTY-LICENSES.txt"
VERSION = f"gamepadla-plus {__version__}"

del metadata
