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
        self.message = "就绪。启动自动化前请保持黑夜君临在前台。"

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
                self._repository("sell", "deepnight")
            elif key == ord("6"):
                self._repository("favorite", "deepnight")
            elif key == ord("7"):
                self._presets("normal")
            elif key == ord("8"):
                self._presets("deepnight")
            elif key == ord("9"):
                self._saves()
            elif key == ord("0"):
                self._diagnostics()

    def _draw_home(self):
        self.screen.erase()
        self._title("NRrelics Deck  |  SSH 终端控制")
        self._lines([
            "1  商店：普通遗物自动筛选",
            "2  商店：深夜遗物自动筛选",
            "3  仓库：出售不合格普通遗物",
            "4  仓库：收藏合格普通遗物",
            "5  仓库：出售不合格深夜遗物",
            "6  仓库：收藏合格深夜遗物",
            "7  普通遗物预设",
            "8  深夜预设与黑名单",
            "9  存档备份与恢复",
            "0  环境诊断",
            "",
            "q / Esc  退出",
            "",
            self.message,
        ], 3)
        self.screen.refresh()

    def _shop(self, mode: str):
        currency = self._ask_int("暗痕低于多少时停止（0 = 不限制）", 5000, minimum=0)
        if currency is None:
            return
        matches = self._ask_int("需要几条有效词条（2 或 3）", 2, minimum=2, maximum=3)
        if matches is None:
            return
        title = "普通遗物商店筛选" if mode == "normal" else "深夜遗物商店筛选"
        self._run_automation(title, "shop", mode, currency, matches)

    def _repository(self, action: str, mode: str):
        count = self._ask_int("处理多少个遗物", 20, minimum=1, maximum=1000)
        if count is None:
            return
        matches = self._ask_int("需要几条有效词条（2 或 3）", 2, minimum=2, maximum=3)
        if matches is None:
            return
        if action == "sell" and not self._confirm("这会确认出售不合格遗物。继续吗？", "出售"):
            self.message = "已取消出售。"
            return
        relic_type = "普通遗物" if mode == "normal" else "深夜遗物"
        verb = "出售" if action == "sell" else "收藏"
        self._run_automation(f"{relic_type}{verb}", "repo", mode, count, matches, action)

    def _run_automation(self, title, kind, mode, number, matches, action=None):
        self._show([f"正在启动{title}。", "按 Ctrl-C 可立即停止。", "", "正在加载原版 OCR 与自动化循环..."])
        curses.def_prog_mode()
        curses.endwin()
        try:
            from .upstream_runner import run_repository, run_shop
            if kind == "shop":
                run_shop(mode, "new", number, matches == 2)
            else:
                run_repository(mode, action, number, matches == 2, False)
            self.message = f"{title}已完成。"
        except KeyboardInterrupt:
            self.message = f"{title}已停止。"
        except Exception as exc:
            self.message = f"{title}失败：{exc}"
        finally:
            curses.reset_prog_mode()
            self.screen.keypad(True)
            self.screen.refresh()

    def _presets(self, mode: str):
        store = PresetStore(self.app_root)
        while True:
            presets = store.list_presets(mode)
            lines = [("普通遗物预设" if mode == "normal" else "深夜遗物预设"), ""]
            for index, preset in enumerate(presets, 1):
                state = "启用" if preset.get("is_active", True) else "停用"
                lines.append(f"{index}. {preset['name']} [{state}] - {len(preset['affixes'])} 条词条")
            lines += ["", "a 添加到通用预设", "r 从通用预设删除", "v 查看通用预设", "b 深夜黑名单" if mode == "deepnight" else "", "Esc 返回"]
            self._show(lines)
            key = self.screen.getch()
            if key in (27, ord("q")):
                return
            if key == ord("a"):
                affix = self._ask("输入词条")
                if affix:
                    self.message = "词条已添加。" if store.add_affix(mode, affix) else "词条已存在。"
            elif key == ord("r"):
                affix = self._ask("输入要删除的词条")
                if affix:
                    self.message = "词条已删除。" if store.remove_affix(mode, affix) else "词条不在预设中。"
            elif key == ord("v"):
                self._show(["通用预设", "", *store.get_general(mode)["affixes"], "", "按任意键返回"])
                self.screen.getch()
            elif mode == "deepnight" and key == ord("b"):
                self._blacklist(store)

    def _blacklist(self, store):
        while True:
            values = store.blacklist()["affixes"]
            self._show(["深夜黑名单", "", *values, "", "a 添加  r 删除  Esc 返回"])
            key = self.screen.getch()
            if key in (27, ord("q")):
                return
            if key == ord("a"):
                value = self._ask("输入要排除的词条")
                if value:
                    store.add_blacklist_affix(value)
            elif key == ord("r"):
                value = self._ask("输入要删除的词条")
                if value:
                    store.remove_blacklist_affix(value)

    def _saves(self):
        steam_root = detect_steam_root()
        users = discover_users(steam_root) if steam_root else []
        if not users:
            self.message = "未找到黑夜君临存档。"
            return
        user = users[0]
        store = SaveStore()
        while True:
            backups = store.list_backups(user.steam_id)
            lines = ["存档备份", f"当前存档：{user.save_path.name}", "", "b 创建备份"]
            lines += [f"{index}. 恢复 {backup.stem}" for index, backup in enumerate(backups, 1)]
            lines += ["", "Esc 返回"]
            self._show(lines)
            key = self.screen.getch()
            if key in (27, ord("q")):
                return
            if key == ord("b"):
                name = self._ask("备份名称", datetime.now().strftime("backup-%Y%m%d-%H%M"))
                if name:
                    try:
                        store.backup(user, name)
                        self.message = "备份已创建。"
                    except Exception as exc:
                        self.message = f"备份失败：{exc}"
            elif ord("1") <= key <= ord("9"):
                index = key - ord("1")
                if index < len(backups) and self._confirm(f"恢复 {backups[index].stem}？", "恢复"):
                    try:
                        store.restore(user, backups[index])
                        self.message = "存档已恢复。"
                    except Exception as exc:
                        self.message = f"恢复失败：{exc}"

    def _diagnostics(self):
        from .deck_session import DeckSession
        session = DeckSession()
        tools = session.available_tools()
        names = {"ffmpeg": "XWayland 截图", "xdotool": "XWayland 键鼠", "grim": "Wayland 截图", "wtype": "Wayland 键盘", "ydotool": "虚拟输入"}
        self._show(["Deck 环境诊断", "", *(f"{names.get(key, key)}：{'就绪' if value else '缺失'}" for key, value in tools.items()), "", "按任意键返回"])
        self.screen.getch()

    def _ask(self, label: str, default: str = "") -> str | None:
        curses.echo()
        self._cursor(True)
        self.screen.erase()
        self._title(label)
        self.screen.addstr(3, 2, f"默认值：{default}")
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
            self.message = "输入无效。"
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
