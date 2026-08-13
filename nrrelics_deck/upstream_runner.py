"""CLI-facing entry points that execute the original NRrelics algorithms."""

from __future__ import annotations

import logging

from .deck_session import DeckSession
from .upstream_adapter import install


def _dependencies(session: DeckSession, log_callback=print):
    log_callback("检查 Deck 截图与键鼠后端…")
    session.require_automation_tools()
    log_callback("连接 XWayland 游戏窗口…")
    install(session)
    # RapidOCR installs a console handler which bypasses the TUI's log queue.
    # Keep the library quiet; original NRrelics workflow messages use callbacks.
    rapidocr_logger = logging.getLogger("RapidOCR")
    rapidocr_logger.handlers.clear()
    rapidocr_logger.addHandler(logging.NullHandler())
    rapidocr_logger.propagate = False
    log_callback("加载 RapidOCR 模型（首次可能需要约半分钟）…")
    from core import OCREngine
    from core.automation import RepositoryFilter
    from core.preset_manager import PresetManager
    from core.relic_detector import RelicDetector

    ocr = OCREngine()
    log_callback("RapidOCR 已就绪。")
    log_callback("加载遗物预设…")
    presets = PresetManager()
    log_callback("初始化商店/仓库控制器…")
    repository_filter = RepositoryFilter(ocr)
    log_callback("自动化控制器已就绪。")
    return ocr, presets, repository_filter, RelicDetector()


def run_shop(mode: str, version: str, stop_currency: int, double: bool, log_callback=print, controller_callback=None) -> None:
    session = DeckSession()
    ocr, presets, repository_filter, _ = _dependencies(session, log_callback)
    from core.shop_automation import ShopAutomation

    controller = ShopAutomation(ocr, presets, repository_filter, {})
    if controller_callback:
        controller_callback(controller)
    controller.start_shopping(mode, version, stop_currency, double, log_callback=lambda message, _level="INFO": log_callback(message))


def run_repository(mode: str, action: str, count: int, double: bool, allow_favorited: bool, log_callback=print, controller_callback=None) -> None:
    session = DeckSession()
    ocr, presets, _, detector = _dependencies(session, log_callback)
    from core.repo_cleaner import RepoCleaner

    controller = RepoCleaner(presets, ocr, detector, {})
    if controller_callback:
        controller_callback(controller)
    controller.start_cleaning(mode, action, count, allow_favorited, double, log_callback=lambda message, _level="INFO": log_callback(message))
