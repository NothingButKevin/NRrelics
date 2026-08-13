"""SSH-first command line interface for the Steam Deck port."""

from __future__ import annotations

import argparse
import cmd
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__
from .deck_session import DeckSession
from .paths import detect_steam_root, discover_users, proton_save_root, user_data_root
from .presets import PresetStore
from .saves import SaveStore


APP_ROOT = Path(__file__).resolve().parent.parent


def _users_or_error() -> tuple[Path, list]:
    steam_root = detect_steam_root()
    if not steam_root:
        raise RuntimeError("Nightreign's SteamOS Proton prefix was not found. Start the game once, then retry.")
    users = discover_users(steam_root)
    if not users:
        raise RuntimeError(f"No Steam users found under {proton_save_root(steam_root)}")
    return steam_root, users


def _select_user(steam_id: str | None):
    _, users = _users_or_error()
    if steam_id:
        for user in users:
            if user.steam_id == steam_id:
                return user
        raise RuntimeError(f"Steam user not found: {steam_id}")
    return users[0]


def _format_bytes(size: int) -> str:
    return f"{size / 1024 / 1024:.1f} MiB"


def command_status(_: argparse.Namespace) -> int:
    steam_root = detect_steam_root()
    print(f"data: {user_data_root()}")
    if not steam_root:
        print("Nightreign Proton prefix: not found")
        return 1
    print(f"steam: {steam_root}")
    print(f"save root: {proton_save_root(steam_root)}")
    users = discover_users(steam_root)
    store = SaveStore()
    for user in users:
        info = store.info(user)
        state = f"{_format_bytes(info.size)}, {info.modified:%Y-%m-%d %H:%M}" if info.exists else "save missing"
        print(f"user {user.steam_id}: {state}")
    return 0


def command_saves(args: argparse.Namespace) -> int:
    user = _select_user(args.user)
    store = SaveStore()
    if args.action == "list":
        info = store.info(user)
        print(f"active: {info.path}")
        print(f"state: {'present' if info.exists else 'missing'}")
        for backup in store.list_backups(user.steam_id):
            print(f"backup: {backup.name} ({_format_bytes(backup.stat().st_size)})")
        return 0
    if args.action == "backup":
        path = store.backup(user, args.name)
        print(f"backup created: {path}")
        return 0
    if not args.yes:
        raise RuntimeError("Restore changes the active save. Re-run with --yes after checking `nrrelics saves list`.")
    backups = store.list_backups(user.steam_id)
    selected = next((path for path in backups if path.name == args.name or path.stem == args.name), None)
    if not selected:
        raise RuntimeError(f"Backup not found: {args.name}")
    path = store.restore(user, selected)
    print(f"save restored: {path}")
    return 0


def command_presets(args: argparse.Namespace) -> int:
    store = PresetStore(APP_ROOT)
    if args.action == "list":
        for preset in store.list_presets(args.mode):
            active = "active" if preset.get("is_active", True) else "disabled"
            print(f"{preset['id']} | {preset['name']} | {active} | {len(preset['affixes'])} affixes")
            for affix in preset["affixes"]:
                print(f"  {affix}")
        return 0
    if args.action == "search":
        for affix in store.search_vocabulary(args.mode, args.query):
            print(affix)
        return 0
    if args.action == "create":
        preset = store.create(args.mode, args.name)
        print(f"created: {preset['id']}")
        return 0
    if args.action == "delete":
        print("deleted" if store.delete(args.mode, args.preset) else "not found")
        return 0
    if args.action in {"enable", "disable"}:
        store.set_active(args.mode, args.preset, args.action == "enable")
        print(args.action + "d")
        return 0
    if args.action in {"add", "remove"}:
        changed = (store.add_affix if args.action == "add" else store.remove_affix)(args.mode, args.affix, args.preset)
        print("updated" if changed else "already absent/present")
        return 0
    if args.action == "blacklist-list":
        for affix in store.blacklist()["affixes"]:
            print(affix)
        return 0
    changed = (store.add_blacklist_affix if args.action == "blacklist-add" else store.remove_blacklist_affix)(args.affix)
    print("updated" if changed else "already absent/present")
    return 0


def command_doctor(_: argparse.Namespace) -> int:
    status = command_status(argparse.Namespace())
    session = DeckSession()
    tools = session.available_tools()
    print(f"python: {sys.version.split()[0]}")
    print("interface: SSH CLI (no GUI required)")
    print(f"OCR packages: {'available' if shutil.which('tesseract') else 'not installed'}")
    print(f"screenshots (grim): {'available' if tools['grim'] else 'not installed'}")
    print(f"Wayland input (wtype): {'available' if tools['wtype'] else 'not installed'}")
    print(f"virtual input (ydotool): {'available' if tools['ydotool'] else 'not installed'}")
    return status


def command_screen(args: argparse.Namespace) -> int:
    path = DeckSession().capture(Path(args.output))
    print(f"screenshot: {path}")
    return 0


def command_input(args: argparse.Namespace) -> int:
    session = DeckSession()
    for _ in range(args.repeat):
        session.key(args.key)
    print(f"sent: {args.key} x{args.repeat}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nrrelics", description="Nightreign relic and save tools for SSH into Steam Deck")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    status = commands.add_parser("status", help="detect SteamOS paths and saves")
    status.set_defaults(handler=command_status)
    doctor = commands.add_parser("doctor", help="show CLI and SteamOS environment diagnostics")
    doctor.set_defaults(handler=command_doctor)
    screen = commands.add_parser("screen", help="capture the currently visible Deck screen")
    screen.add_argument("output", nargs="?", default="~/Pictures/nrrelics-screen.png")
    screen.set_defaults(handler=command_screen)
    input_command = commands.add_parser("input", help="send one key to the current focused Deck window")
    input_command.add_argument("key", choices=("f", "m", "0", "1", "2", "3", "4", "5", "left", "right", "up", "down", "enter", "escape"))
    input_command.add_argument("--repeat", type=int, default=1, choices=range(1, 101), metavar="1..100")
    input_command.set_defaults(handler=command_input)
    saves = commands.add_parser("saves", help="list, back up, or restore saves")
    saves.add_argument("--user", help="SteamID64; defaults to the first detected user")
    saves_sub = saves.add_subparsers(dest="action", required=True)
    saves_sub.add_parser("list").set_defaults(handler=command_saves)
    backup = saves_sub.add_parser("backup")
    backup.add_argument("--name", help="backup label")
    backup.set_defaults(handler=command_saves)
    restore = saves_sub.add_parser("restore")
    restore.add_argument("name", help="backup filename or label")
    restore.add_argument("--yes", action="store_true", help="confirm active-save replacement")
    restore.set_defaults(handler=command_saves)
    presets = commands.add_parser("presets", help="manage compatible relic OCR presets")
    presets.add_argument("mode", choices=("normal", "deepnight"))
    presets_sub = presets.add_subparsers(dest="action", required=True)
    presets_sub.add_parser("list").set_defaults(handler=command_presets)
    search = presets_sub.add_parser("search")
    search.add_argument("query")
    search.set_defaults(handler=command_presets)
    create = presets_sub.add_parser("create")
    create.add_argument("name")
    create.set_defaults(handler=command_presets)
    delete = presets_sub.add_parser("delete")
    delete.add_argument("preset")
    delete.set_defaults(handler=command_presets)
    for action in ("enable", "disable"):
        action_parser = presets_sub.add_parser(action)
        action_parser.add_argument("preset")
        action_parser.set_defaults(handler=command_presets)
    for action in ("add", "remove"):
        action_parser = presets_sub.add_parser(action)
        action_parser.add_argument("affix")
        action_parser.add_argument("--preset", default="general", help="general or a dedicated preset ID")
        action_parser.set_defaults(handler=command_presets)
    black_list = presets_sub.add_parser("blacklist-list")
    black_list.set_defaults(handler=command_presets)
    for action in ("blacklist-add", "blacklist-remove"):
        action_parser = presets_sub.add_parser(action)
        action_parser.add_argument("affix")
        action_parser.set_defaults(handler=command_presets)
    shell = commands.add_parser("shell", help="start an interactive terminal session")
    shell.set_defaults(handler=lambda _: DeckShell().cmdloop())
    return parser


class DeckShell(cmd.Cmd):
    intro = "NRrelics Deck CLI. Type `help` for commands, `exit` to leave."
    prompt = "nrrelics> "

    def default(self, line: str):
        if line in {"exit", "quit"}:
            return True
        try:
            args = build_parser().parse_args(shlex.split(line))
            return args.handler(args)
        except SystemExit:
            return False
        except Exception as exc:
            print(f"error: {exc}")
            return False

    def do_exit(self, _: str):
        return True

    do_quit = do_exit

    def do_help(self, _: str):
        print("Commands: status, doctor, screen [PATH], input KEY, saves ..., presets ..., exit")
        print("Examples: saves backup --name before-cleanup | presets normal list")


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        result = args.handler(args)
        return result if isinstance(result, int) else 0
    except (RuntimeError, FileNotFoundError, FileExistsError, ValueError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
