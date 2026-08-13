"""CLI-facing entry points that execute the original NRrelics algorithms."""

from __future__ import annotations

from .deck_session import DeckSession
from .upstream_adapter import install


def _dependencies(session: DeckSession):
    session.require_automation_tools()
    install(session)
    from core import OCREngine
    from core.automation import RepositoryFilter
    from core.preset_manager import PresetManager
    from core.relic_detector import RelicDetector

    ocr = OCREngine()
    presets = PresetManager()
    repository_filter = RepositoryFilter(ocr)
    return ocr, presets, repository_filter, RelicDetector()


def run_shop(mode: str, version: str, stop_currency: int, double: bool) -> None:
    session = DeckSession()
    ocr, presets, repository_filter, _ = _dependencies(session)
    from core.shop_automation import ShopAutomation

    controller = ShopAutomation(ocr, presets, repository_filter, {})
    controller.start_shopping(mode, version, stop_currency, double, log_callback=lambda message, _level="INFO": print(message, flush=True))


def run_repository(mode: str, action: str, count: int, double: bool, allow_favorited: bool) -> None:
    session = DeckSession()
    ocr, presets, _, detector = _dependencies(session)
    from core.repo_cleaner import RepoCleaner

    controller = RepoCleaner(presets, ocr, detector, {})
    controller.start_cleaning(mode, action, count, allow_favorited, double, log_callback=lambda message, _level="INFO": print(message, flush=True))
