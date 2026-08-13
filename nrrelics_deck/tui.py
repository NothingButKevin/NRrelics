"""Dependency-free SSH terminal UI for NRrelics Deck."""

from __future__ import annotations

import curses
from datetime import datetime

from .paths import detect_steam_root, discover_users
from .presets import PresetStore
from .saves import SaveStore


class App:
    def __init__(self, screen, app_root):
        self.screen = screen
        self.app_root = app_root
        self.message = "Ready. Keep Nightreign focused before starting automation."

    def run(self):
        self._cursor(False)
        self.screen.keypad(True)
        while True:
            self._draw_home()
            key = self.screen.getch()
            if key in (ord("q"), 27):
                return
            if key == ord("1"):
                self._shop("normal")
            elif key == ord("2"):
                self._shop("deepnight")
            elif key == ord("3"):
                self._repository("sell", "normal")
            elif key == ord("4"):
                self._repository("favorite", "normal")
            elif key == ord("5"):
                self._presets("normal")
            elif key == ord("6"):
                self._presets("deepnight")
            elif key == ord("7"):
                self._saves()
            elif key == ord("8"):
                self._diagnostics()

    def _draw_home(self):
        self.screen.erase()
        self._title("NRrelics Deck  |  SSH Terminal Control")
        self._lines([
            "1  Shop: normal relics",
            "2  Shop: deepnight relics",
            "3  Repository: sell unmatched normal relics",
            "4  Repository: favorite matched normal relics",
            "5  Normal presets",
            "6  Deepnight presets and blacklist",
            "7  Save backups",
            "8  Diagnostics",
            "",
            "q / Esc  Exit",
            "",
            self.message,
        ], 3)
        self.screen.refresh()

    def _shop(self, mode: str):
        currency = self._ask_int("Stop when currency is below (0 = never)", 5000, minimum=0)
        if currency is None:
            return
        matches = self._ask_int("Required good affixes (2 or 3)", 2, minimum=2, maximum=3)
        if matches is None:
            return
        self._run_automation(f"Shop {mode}", "shop", mode, currency, matches)

    def _repository(self, action: str, mode: str):
        count = self._ask_int("How many relics to process", 20, minimum=1, maximum=1000)
        if count is None:
            return
        matches = self._ask_int("Required good affixes (2 or 3)", 2, minimum=2, maximum=3)
        if matches is None:
            return
        if action == "sell" and not self._confirm("This will confirm selling unmatched relics. Continue?", "SELL"):
            self.message = "Sale cancelled."
            return
        self._run_automation(f"Repository {action}", "repo", mode, count, matches, action)

    def _run_automation(self, title, kind, mode, number, matches, action=None):
        self._show([f"{title} is starting.", "Press Ctrl-C in this SSH terminal to stop.", "", "Loading original OCR and automation loop..."])
        curses.def_prog_mode()
        curses.endwin()
        try:
            from .upstream_runner import run_repository, run_shop
            if kind == "shop":
                run_shop(mode, "new", number, matches == 2)
            else:
                run_repository(mode, action, number, matches == 2, False)
            self.message = f"{title} completed."
        except KeyboardInterrupt:
            self.message = f"{title} stopped."
        except Exception as exc:
            self.message = f"{title} failed: {exc}"
        finally:
            self.screen.refresh()
            curses.reset_prog_mode()
            self.screen.keypad(True)

    def _presets(self, mode: str):
        store = PresetStore(self.app_root)
        while True:
            presets = store.list_presets(mode)
            lines = [f"{mode.title()} presets", ""]
            for index, preset in enumerate(presets, 1):
                state = "on" if preset.get("is_active", True) else "off"
                lines.append(f"{index}. {preset['name']} [{state}] - {len(preset['affixes'])} affixes")
            lines += ["", "a Add affix to general preset", "r Remove affix from general preset", "v View general affixes", "b Deepnight blacklist" if mode == "deepnight" else "", "Esc Back"]
            self._show(lines)
            key = self.screen.getch()
            if key in (27, ord("q")):
                return
            if key == ord("a"):
                affix = self._ask("Affix text")
                if affix:
                    self.message = "Affix added." if store.add_affix(mode, affix) else "Affix is already present."
            elif key == ord("r"):
                affix = self._ask("Affix text to remove")
                if affix:
                    self.message = "Affix removed." if store.remove_affix(mode, affix) else "Affix was not present."
            elif key == ord("v"):
                self._show(["General preset", "", *store.get_general(mode)["affixes"], "", "Any key to return"])
                self.screen.getch()
            elif mode == "deepnight" and key == ord("b"):
                self._blacklist(store)

    def _blacklist(self, store):
        while True:
            values = store.blacklist()["affixes"]
            self._show(["Deepnight blacklist", "", *values, "", "a Add  r Remove  Esc Back"])
            key = self.screen.getch()
            if key in (27, ord("q")):
                return
            if key == ord("a"):
                value = self._ask("Affix to reject")
                if value:
                    store.add_blacklist_affix(value)
            elif key == ord("r"):
                value = self._ask("Affix to remove")
                if value:
                    store.remove_blacklist_affix(value)

    def _saves(self):
        steam_root = detect_steam_root()
        users = discover_users(steam_root) if steam_root else []
        if not users:
            self.message = "No Nightreign save found."
            return
        user = users[0]
        store = SaveStore()
        while True:
            backups = store.list_backups(user.steam_id)
            lines = ["Save backups", f"Active: {user.save_path.name}", "", "b Create backup"]
            lines += [f"{index}. Restore {backup.stem}" for index, backup in enumerate(backups, 1)]
            lines += ["", "Esc Back"]
            self._show(lines)
            key = self.screen.getch()
            if key in (27, ord("q")):
                return
            if key == ord("b"):
                name = self._ask("Backup name", datetime.now().strftime("backup-%Y%m%d-%H%M"))
                if name:
                    try:
                        store.backup(user, name)
                        self.message = "Backup created."
                    except Exception as exc:
                        self.message = f"Backup failed: {exc}"
            elif ord("1") <= key <= ord("9"):
                index = key - ord("1")
                if index < len(backups) and self._confirm(f"Restore {backups[index].stem}?", "RESTORE"):
                    try:
                        store.restore(user, backups[index])
                        self.message = "Save restored."
                    except Exception as exc:
                        self.message = f"Restore failed: {exc}"

    def _diagnostics(self):
        from .deck_session import DeckSession
        session = DeckSession()
        tools = session.available_tools()
        self._show(["Deck diagnostics", "", *(f"{key}: {'ready' if value else 'missing'}" for key, value in tools.items()), "", "Any key to return"])
        self.screen.getch()

    def _ask(self, label: str, default: str = "") -> str | None:
        curses.echo()
        self._cursor(True)
        self.screen.erase()
        self._title(label)
        self.screen.addstr(3, 2, f"Default: {default}")
        self.screen.addstr(5, 2, "> ")
        self.screen.refresh()
        value = self.screen.getstr(5, 4).decode(errors="replace").strip()
        curses.noecho()
        self._cursor(False)
        return value or default

    def _ask_int(self, label: str, default: int, minimum: int, maximum: int | None = None) -> int | None:
        value = self._ask(label, str(default))
        try:
            parsed = int(value)
            if parsed < minimum or (maximum is not None and parsed > maximum):
                raise ValueError
            return parsed
        except (TypeError, ValueError):
            self.message = "Invalid value."
            return None

    def _confirm(self, message: str, token: str) -> bool:
        value = self._ask(f"{message} Type {token} to confirm")
        return value == token

    def _show(self, lines):
        self.screen.erase()
        self._title("NRrelics Deck")
        self._lines(lines, 3)
        self.screen.refresh()

    def _title(self, text):
        self.screen.addstr(0, 2, text, curses.A_BOLD)
        self.screen.hline(1, 0, "-", max(1, curses.COLS - 1))

    def _lines(self, lines, row):
        for line in lines:
            if row >= curses.LINES - 1:
                break
            self.screen.addnstr(row, 2, str(line), max(1, curses.COLS - 4))
            row += 1

    @staticmethod
    def _cursor(visible: bool):
        try:
            curses.curs_set(int(visible))
        except curses.error:
            pass


def run(app_root):
    curses.wrapper(lambda screen: App(screen, app_root).run())
