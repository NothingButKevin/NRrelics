import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from nrrelics_deck.deck_session import DeckSession


class DeckSessionTests(unittest.TestCase):
    def test_key_uses_xdotool_when_available(self):
        calls = []

        def runner(*args, **kwargs):
            calls.append((args, kwargs))

        session = DeckSession(runner=runner)
        with patch("nrrelics_deck.deck_session.shutil.which", side_effect=lambda tool: "/bin/" + tool if tool == "xdotool" else None):
            session.key("f")

        self.assertEqual(calls[0][0][0], ["xdotool", "key", "f"])

    def test_capture_requires_a_backend(self):
        session = DeckSession()
        with TemporaryDirectory() as directory, patch("nrrelics_deck.deck_session.shutil.which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "capture"):
                session.capture(Path(directory) / "screen.png")

    def test_mouse_uses_xdotool_when_available(self):
        calls = []

        def runner(*args, **kwargs):
            calls.append((args, kwargs))

        session = DeckSession(runner=runner)
        with patch("nrrelics_deck.deck_session.shutil.which", side_effect=lambda tool: "/bin/" + tool if tool == "xdotool" else None):
            session.move_mouse(100, 200)

        self.assertEqual(calls[0][0][0], ["xdotool", "mousemove", "100", "200"])
