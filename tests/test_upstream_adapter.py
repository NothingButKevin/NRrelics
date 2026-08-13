import sys
import unittest
from unittest.mock import patch

from nrrelics_deck.upstream_adapter import install


class _Image:
    size = (1280, 720)


class _Session:
    def screenshot(self, region=None):
        return _Image()

    def key(self, _key):
        pass

    def move_mouse(self, _x, _y):
        pass

    def click(self):
        pass


class UpstreamAdapterTests(unittest.TestCase):
    def test_installs_modules_expected_by_original_automation(self):
        with patch.dict(sys.modules, {}, clear=False):
            install(_Session())
            import pyautogui
            import pydirectinput
            import pygetwindow
            import win32gui

            self.assertEqual(pygetwindow.getAllWindows()[0].width, 1280)
            self.assertEqual(win32gui.GetClientRect(1), (0, 0, 1280, 720))
            self.assertTrue(callable(pyautogui.screenshot))
            self.assertTrue(callable(pydirectinput.press))
