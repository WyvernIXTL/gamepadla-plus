from importlib import metadata
from os import environ

__version__ = metadata.version(__package__)
environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

LICENSE_FILE_NAME = "LICENSE.txt"
THIRD_PARTY_LICENSE_FILE_NAME = "THIRD-PARTY-LICENSES.txt"
VERSION = f"gamepadla-plus {__version__}"

del metadata
