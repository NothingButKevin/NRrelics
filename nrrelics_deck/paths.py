"""SteamOS and Proton path discovery."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


NIGHTREIGN_APP_ID = "2622380"
SAVE_NAME = "NR0000.sl2"


def _unique(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    result: list[Path] = []
    for path in paths:
        expanded = path.expanduser()
        if expanded not in seen:
            seen.add(expanded)
            result.append(expanded)
    return result


def steam_roots() -> list[Path]:
    """Return Steam install directories commonly used by SteamOS and Linux."""
    configured = os.environ.get("NRRELICS_STEAM_ROOT")
    roots = [
        Path(configured) if configured else Path("/nonexistent"),
        Path("~/.local/share/Steam"),
        Path("~/.steam/steam"),
    ]
    return _unique(roots)


def detect_steam_root() -> Path | None:
    for root in steam_roots():
        if (root / "steamapps" / "compatdata" / NIGHTREIGN_APP_ID).is_dir():
            return root
    return None


def proton_save_root(steam_root: Path) -> Path:
    return (
        steam_root
        / "steamapps"
        / "compatdata"
        / NIGHTREIGN_APP_ID
        / "pfx"
        / "drive_c"
        / "users"
        / "steamuser"
        / "AppData"
        / "Roaming"
        / "Nightreign"
    )


def user_data_root() -> Path:
    configured = os.environ.get("NRRELICS_DATA_DIR")
    if configured:
        return Path(configured).expanduser()
    xdg_data = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data).expanduser() if xdg_data else Path("~/.local/share").expanduser()
    return base / "nrrelics-deck"


@dataclass(frozen=True)
class SteamUser:
    steam_id: str
    save_path: Path


def discover_users(steam_root: Path) -> list[SteamUser]:
    root = proton_save_root(steam_root)
    if not root.is_dir():
        return []
    users = [SteamUser(path.name, path / SAVE_NAME) for path in root.iterdir() if path.is_dir() and path.name.isdigit()]
    return sorted(users, key=lambda user: (not user.save_path.exists(), user.steam_id))
