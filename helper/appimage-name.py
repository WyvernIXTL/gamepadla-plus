from platform import machine

from gamepadla_plus.__about__ import __version__

match machine():
    case "x86" | "x86_64" | "AMD64":
        print(f"gamepadla-plus-v{__version__}-linux-x64.AppImage")
    case "arm64" | "aarch64":
        print(f"gamepadla-plus-v{__version__}-linux-arm64.AppImage")
