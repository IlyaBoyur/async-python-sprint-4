import logging

import pyshorteners

from core.config import app_settings

logger = logging.getLogger(__name__)


def generate_short_url(original: str) -> str:
    shortener = getattr(
        pyshorteners.Shortener(), app_settings.project_shortener, None
    )
    if shortener is None:
        raise RuntimeError("Shortener is not configured or incorrect")
    short = shortener.short(url=original)
    logger.info(f"url shortened: {original} -> {short}")
    return short
