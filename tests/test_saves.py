import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nrrelics_deck.paths import SteamUser
from nrrelics_deck.saves import SaveStore


class SaveStoreTests(unittest.TestCase):
    def test_backup_and_restore_preserves_a_safety_copy(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            active = root / "Nightreign" / "765" / "NR0000.sl2"
            active.parent.mkdir(parents=True)
            active.write_bytes(b"original")
            user = SteamUser("765", active)
            store = SaveStore(root / "data")

            backup = store.backup(user, "before-test")
            active.write_bytes(b"changed")
            restored = store.restore(user, backup)

            self.assertEqual(restored.read_bytes(), b"original")
            self.assertEqual(list(active.parent.glob("NR0000.sl2.before-restore-*"))[0].read_bytes(), b"changed")

    def test_restore_rejects_outside_backup_directory(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            user = SteamUser("765", root / "save.sl2")
            user.save_path.write_bytes(b"active")
            outside = root / "outside.sl2"
            outside.write_bytes(b"backup")
            store = SaveStore(root / "data")

            with self.assertRaises(ValueError):
                store.restore(user, outside)
