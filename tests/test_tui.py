import unittest
from unittest.mock import patch

from nrrelics_deck import tui


class TuiTests(unittest.TestCase):
    def test_run_wraps_the_application(self):
        seen = []

        def wrapper(callback):
            seen.append(callback)

        with patch("nrrelics_deck.tui.curses.wrapper", wrapper):
            tui.run("/tmp/app")

        self.assertEqual(len(seen), 1)

    def test_confirmation_requires_exact_token(self):
        app = object.__new__(tui.App)
        app._ask = lambda _label: "NO"
        self.assertFalse(app._confirm("Confirm", "SELL"))
        app._ask = lambda _label: "SELL"
        self.assertTrue(app._confirm("Confirm", "SELL"))

    def test_home_dispatches_deepnight_repository(self):
        app = object.__new__(tui.App)
        app._cursor = lambda _visible: None
        app._draw_home = lambda: None
        app._repository = lambda action, mode: calls.append((action, mode))
        calls = []

        class Screen:
            def keypad(self, _enabled):
                pass

            def getch(self):
                return ord("5") if not calls else ord("q")

        app.screen = Screen()
        app.run()

        self.assertEqual(calls, [("sell", "deepnight")])

    def test_log_view_keeps_status_in_a_separate_panel(self):
        calls = []

        class Screen:
            def erase(self):
                calls.append("erase")

            def vline(self, *_args):
                calls.append("vline")

            def addstr(self, *_args):
                calls.append("addstr")

            def addnstr(self, *_args):
                calls.append("addnstr")

            def refresh(self):
                calls.append("refresh")

            def getmaxyx(self):
                return (30, 100)

        app = object.__new__(tui.App)
        app.screen = Screen()
        app._title = lambda _text: calls.append("title")
        app._draw_log_view("商店", "shop", "normal", 5000, 2, ["第一条日志"], False)

        self.assertIn("vline", calls)
        self.assertIn("refresh", calls)
