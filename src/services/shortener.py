import logging

import pyshorteners

from core.config import PROJECT_SHORTENER

logger = logging.getLogger(__name__)


def generate_short_url(original: str) -> str:
    if (
        shortener := getattr(pyshorteners.Shortener(), PROJECT_SHORTENER, None)
    ) is None:
        raise RuntimeError("Shortener is not configured or incorrect")
    short = shortener.short(url=original)
    logger.info(f"url shortened: {original} -> {short}")
    return short
