"""Safe local save backup and restore operations."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .paths import SAVE_NAME, SteamUser, user_data_root


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    return cleaned.strip(".-") or _stamp()


@dataclass(frozen=True)
class SaveInfo:
    steam_id: str
    path: Path
    exists: bool
    size: int
    modified: datetime | None


class SaveStore:
    def __init__(self, data_root: Path | None = None):
        self.data_root = data_root or user_data_root()

    def info(self, user: SteamUser) -> SaveInfo:
        path = user.save_path
        if not path.exists():
            return SaveInfo(user.steam_id, path, False, 0, None)
        stat = path.stat()
        return SaveInfo(user.steam_id, path, True, stat.st_size, datetime.fromtimestamp(stat.st_mtime))

    def backup_dir(self, steam_id: str) -> Path:
        return self.data_root / "backups" / steam_id

    def list_backups(self, steam_id: str) -> list[Path]:
        directory = self.backup_dir(steam_id)
        if not directory.exists():
            return []
        return sorted(directory.glob("*.sl2"), key=lambda path: path.stat().st_mtime, reverse=True)

    def backup(self, user: SteamUser, name: str | None = None) -> Path:
        if not user.save_path.is_file():
            raise FileNotFoundError(f"save not found: {user.save_path}")
        directory = self.backup_dir(user.steam_id)
        directory.mkdir(parents=True, exist_ok=True)
        label = _safe_name(name or _stamp())
        destination = directory / f"{label}.sl2"
        if destination.exists():
            raise FileExistsError(f"backup already exists: {destination.name}")
        shutil.copy2(user.save_path, destination)
        return destination

    def restore(self, user: SteamUser, backup: Path) -> Path:
        backup = backup.expanduser().resolve()
        allowed_dir = self.backup_dir(user.steam_id).resolve()
        if allowed_dir not in backup.parents or backup.suffix != ".sl2":
            raise ValueError("backup must be an .sl2 file in this user's backup directory")
        if not backup.is_file():
            raise FileNotFoundError(f"backup not found: {backup}")
        user.save_path.parent.mkdir(parents=True, exist_ok=True)
        if user.save_path.exists():
            safety_copy = user.save_path.with_suffix(user.save_path.suffix + f".before-restore-{_stamp()}")
            shutil.copy2(user.save_path, safety_copy)
        shutil.copy2(backup, user.save_path)
        return user.save_path
