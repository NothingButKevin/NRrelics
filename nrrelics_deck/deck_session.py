"""Small SteamOS Wayland bridge used from an SSH session.

The bridge intentionally sends input only when explicitly requested.  It does
not create windows and relies on the currently focused game window.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable


Run = Callable[..., subprocess.CompletedProcess[str]]


class DeckSession:
    def __init__(self, runner: Run = subprocess.run):
        self.runner = runner

    def environment(self) -> dict[str, str]:
        environment = os.environ.copy()
        uid = str(os.getuid())
        environment.setdefault("XDG_RUNTIME_DIR", f"/run/user/{uid}")
        environment.setdefault("WAYLAND_DISPLAY", "wayland-0")
        return environment

    def available_tools(self) -> dict[str, bool]:
        return {name: shutil.which(name) is not None for name in ("grim", "wtype", "ydotool")}

    def require_automation_tools(self) -> None:
        tools = self.available_tools()
        missing = []
        if not tools["grim"]:
            missing.append("grim (screenshots)")
        if not tools["ydotool"]:
            missing.append("ydotool (keyboard and mouse input)")
        if missing:
            raise RuntimeError("Deck automation requires " + " and ".join(missing))

    def capture_bytes(self) -> bytes:
        if not shutil.which("grim"):
            raise RuntimeError("grim is required for screenshots; install it on the Deck first")
        result = self.runner(["grim", "-"], check=True, capture_output=True, env=self.environment())
        if not result.stdout:
            raise RuntimeError("grim returned an empty screenshot")
        return result.stdout

    def screenshot(self, region: tuple[int, int, int, int] | None = None):
        try:
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError("Pillow is required for Deck screenshots; run `pip install .[deck]`") from exc
        from io import BytesIO

        image = Image.open(BytesIO(self.capture_bytes())).convert("RGB")
        if region:
            left, top, width, height = region
            image = image.crop((left, top, left + width, top + height))
        return image

    def capture(self, destination: Path) -> Path:
        if not shutil.which("grim"):
            raise RuntimeError("grim is required for screenshots; install it on the Deck first")
        destination = destination.expanduser()
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.runner(["grim", str(destination)], check=True, text=True, capture_output=True, env=self.environment())
        if not destination.is_file():
            raise RuntimeError("grim completed without creating a screenshot")
        return destination

    def key(self, key: str) -> None:
        key = key.lower()
        tools = self.available_tools()
        if tools["ydotool"]:
            code = _YDOTOOL_KEYS.get(key)
            if code is None:
                raise ValueError(f"unsupported ydotool key: {key}")
            self.runner(["ydotool", "key", f"{code}:1", f"{code}:0"], check=True, text=True, capture_output=True)
            return
        if tools["wtype"]:
            self.runner(["wtype", "-k", key], check=True, text=True, capture_output=True, env=self.environment())
            return
        raise RuntimeError("an input backend is required: install wtype or ydotool on the Deck")

    def move_mouse(self, x: int, y: int) -> None:
        if not shutil.which("ydotool"):
            raise RuntimeError("ydotool is required for mouse movement on the Deck")
        self.runner(["ydotool", "mousemove", "--absolute", "-x", str(x), "-y", str(y)], check=True, text=True, capture_output=True)

    def click(self) -> None:
        if not shutil.which("ydotool"):
            raise RuntimeError("ydotool is required for mouse clicks on the Deck")
        self.runner(["ydotool", "click", "0xC0"], check=True, text=True, capture_output=True)


# Linux input-event key codes. wtype is preferred because it accepts names.
_YDOTOOL_KEYS = {
    "f": 33,
    "f1": 59,
    "f2": 60,
    "m": 50,
    "0": 11,
    "1": 2,
    "2": 3,
    "3": 4,
    "4": 5,
    "5": 6,
    "left": 105,
    "right": 106,
    "up": 103,
    "down": 108,
    "enter": 28,
    "escape": 1,
    "q": 16,
}
