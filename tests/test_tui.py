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
