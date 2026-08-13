import unittest
import subprocess
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

    def test_capture_retries_transient_ffmpeg_failure(self):
        calls = []

        def runner(*args, **kwargs):
            calls.append((args, kwargs))
            if len(calls) == 1:
                raise subprocess.CalledProcessError(127, ["ffmpeg"], stderr=b"temporary X11 error")
            return type("Result", (), {"stdout": b"png"})()

        session = DeckSession(runner=runner)
        with patch("nrrelics_deck.deck_session.shutil.which", side_effect=lambda tool: "/usr/bin/ffmpeg" if tool == "ffmpeg" else None), patch("nrrelics_deck.deck_session.time.sleep"):
            self.assertEqual(session.capture_bytes(), b"png")

        self.assertEqual(len(calls), 2)

    def test_ffmpeg_does_not_inherit_opencv_library_path(self):
        session = DeckSession()
        with patch.dict("nrrelics_deck.deck_session.os.environ", {"LD_LIBRARY_PATH": "/opencv/lib"}, clear=True):
            environment = session._system_environment()

        self.assertNotIn("LD_LIBRARY_PATH", environment)
