import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nrrelics_deck.presets import PresetStore


class PresetStoreTests(unittest.TestCase):
    def test_preserves_compatible_schema_and_dedicated_presets(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            store = PresetStore(root, root / "state")

            self.assertTrue(store.add_affix("normal", "攻击力提升"))
            preset = store.create("normal", "Tank")
            self.assertTrue(store.add_affix("normal", "生命力提升", preset["id"]))
            store.set_active("normal", preset["id"], False)

            data = store.load()
            self.assertEqual(data["normal_general"]["affixes"], ["攻击力提升"])
            self.assertEqual(data["normal_dedicated"][preset["id"]]["affixes"], ["生命力提升"])
            self.assertFalse(data["normal_dedicated"][preset["id"]]["is_active"])
