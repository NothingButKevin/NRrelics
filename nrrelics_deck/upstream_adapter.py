"""SteamOS compatibility shims for NRrelics' original automation modules."""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

from .deck_session import DeckSession


class _Window:
    title = "ELDEN RING NIGHTREIGN"
    left = 0
    top = 0

    def __init__(self, session: DeckSession):
        image = session.screenshot()
        self.width, self.height = image.size


def install(session: DeckSession) -> None:
    """Install only the Windows API surface the unchanged upstream code uses."""
    window = _Window(session)
    pyautogui = ModuleType("pyautogui")
    pyautogui.screenshot = session.screenshot
    pyautogui.moveTo = lambda x, y: session.move_mouse(int(x), int(y))
    pyautogui.click = lambda *args, **kwargs: session.click()
    pydirectinput = ModuleType("pydirectinput")
    pydirectinput.press = session.key
    keyboard = ModuleType("keyboard")
    keyboard.add_hotkey = lambda *args, **kwargs: None
    keyboard.remove_hotkey = lambda *args, **kwargs: None
    pygetwindow = ModuleType("pygetwindow")
    # The unchanged upstream annotations reference this Windows-only class
    # while importing the automation module.
    pygetwindow.Win32Window = _Window
    pygetwindow.getAllWindows = lambda: [window]
    win32gui = ModuleType("win32gui")
    win32gui.FindWindow = lambda *args: 1
    win32gui.GetClientRect = lambda *args: (0, 0, window.width, window.height)
    win32gui.ClientToScreen = lambda *args: (0, 0)
    win32con = ModuleType("win32con")
    sys.modules.update({
        "pyautogui": pyautogui,
        "pydirectinput": pydirectinput,
        "keyboard": keyboard,
        "pygetwindow": pygetwindow,
        "win32gui": win32gui,
        "win32con": win32con,
    })
