import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nrrelics_deck.paths import NIGHTREIGN_APP_ID, discover_users, proton_save_root


class PathTests(unittest.TestCase):
    def test_discovers_proton_users(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "Steam"
            save = proton_save_root(root) / "7656119" / "NR0000.sl2"
            save.parent.mkdir(parents=True)
            save.write_bytes(b"save")

            users = discover_users(root)

            self.assertEqual([(user.steam_id, user.save_path) for user in users], [("7656119", save)])
            self.assertIn(NIGHTREIGN_APP_ID, str(save))
