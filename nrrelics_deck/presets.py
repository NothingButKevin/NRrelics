"""Compatible, terminal-friendly management of NRrelics presets."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from .paths import user_data_root


VOCABULARY_FILES = {
    "normal": ("normal.txt", "normal_special.txt"),
    "deepnight": ("deepnight_pos.txt", "deepnight_neg.txt"),
}


def _default_preset(identifier: str, name: str, preset_type: str, *, general: bool) -> dict:
    return {
        "id": identifier,
        "name": name,
        "type": preset_type,
        "affixes": [],
        "is_general": general,
        "is_active": True,
    }


def default_data() -> dict:
    """Match the original GUI's presets.json schema so settings remain portable."""
    return {
        "version": "1.0",
        "normal_general": _default_preset("normal_general", "普通通用预设", "normal_whitelist", general=True),
        "deepnight_general": _default_preset("deepnight_general", "深夜通用预设", "deepnight_whitelist", general=True),
        "normal_dedicated": {},
        "deepnight_whitelist_dedicated": {},
        "deepnight_blacklist": _default_preset("deepnight_blacklist", "深夜黑名单", "deepnight_blacklist", general=False),
    }


class PresetStore:
    def __init__(self, app_root: Path, data_root: Path | None = None):
        self.app_root = app_root
        self.path = (data_root or user_data_root()) / "presets.json"

    def load(self) -> dict:
        data = default_data()
        if not self.path.exists():
            return data
        with self.path.open(encoding="utf-8") as handle:
            loaded = json.load(handle)
        if not isinstance(loaded, dict):
            raise ValueError(f"invalid presets file: {self.path}")
        for key, value in loaded.items():
            if key in data and isinstance(data[key], dict) and isinstance(value, dict):
                data[key].update(value)
            else:
                data[key] = value
        return data

    def save(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".json.tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        temporary.replace(self.path)

    def _general_key(self, mode: str) -> str:
        return f"{mode}_general"

    def _dedicated_key(self, mode: str) -> str:
        return "normal_dedicated" if mode == "normal" else "deepnight_whitelist_dedicated"

    def get_general(self, mode: str) -> dict:
        return self.load()[self._general_key(mode)]

    def list_presets(self, mode: str) -> list[dict]:
        data = self.load()
        return [data[self._general_key(mode)], *data[self._dedicated_key(mode)].values()]

    def add_affix(self, mode: str, affix: str, preset_id: str = "general") -> bool:
        data = self.load()
        preset = self._find_preset(data, mode, preset_id)
        if affix in preset["affixes"]:
            return False
        preset["affixes"].append(affix)
        self.save(data)
        return True

    def remove_affix(self, mode: str, affix: str, preset_id: str = "general") -> bool:
        data = self.load()
        preset = self._find_preset(data, mode, preset_id)
        if affix not in preset["affixes"]:
            return False
        preset["affixes"].remove(affix)
        self.save(data)
        return True

    def create(self, mode: str, name: str) -> dict:
        data = self.load()
        dedicated = data[self._dedicated_key(mode)]
        if len(dedicated) >= 20:
            raise ValueError("a mode may contain at most 20 dedicated presets")
        identifier = str(uuid.uuid4())
        preset_type = "normal_whitelist" if mode == "normal" else "deepnight_whitelist"
        preset = _default_preset(identifier, name, preset_type, general=False)
        dedicated[identifier] = preset
        self.save(data)
        return preset

    def delete(self, mode: str, preset_id: str) -> bool:
        if preset_id == "general":
            raise ValueError("the general preset cannot be deleted")
        data = self.load()
        dedicated = data[self._dedicated_key(mode)]
        if preset_id not in dedicated:
            return False
        del dedicated[preset_id]
        self.save(data)
        return True

    def set_active(self, mode: str, preset_id: str, active: bool) -> None:
        data = self.load()
        preset = self._find_preset(data, mode, preset_id)
        preset["is_active"] = active
        self.save(data)

    def blacklist(self) -> dict:
        return self.load()["deepnight_blacklist"]

    def add_blacklist_affix(self, affix: str) -> bool:
        data = self.load()
        affixes = data["deepnight_blacklist"]["affixes"]
        if affix in affixes:
            return False
        affixes.append(affix)
        self.save(data)
        return True

    def remove_blacklist_affix(self, affix: str) -> bool:
        data = self.load()
        affixes = data["deepnight_blacklist"]["affixes"]
        if affix not in affixes:
            return False
        affixes.remove(affix)
        self.save(data)
        return True

    def _find_preset(self, data: dict, mode: str, preset_id: str) -> dict:
        if preset_id == "general":
            return data[self._general_key(mode)]
        preset = data[self._dedicated_key(mode)].get(preset_id)
        if not preset:
            raise ValueError(f"preset not found: {preset_id}")
        return preset

    def search_vocabulary(self, mode: str, query: str) -> list[str]:
        query = query.casefold()
        entries: list[str] = []
        for filename in VOCABULARY_FILES[mode]:
            path = self.app_root / "data" / filename
            if not path.exists():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                value = line.split("→", 1)[-1].strip()
                if value and query in value.casefold() and value not in entries:
                    entries.append(value)
        return entries
