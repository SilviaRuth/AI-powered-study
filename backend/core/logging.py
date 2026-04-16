"""Logging setup."""

from __future__ import annotations

import logging

from backend.core.config import get_settings


def configure_logging() -> None:
    """Configure a simple application logger."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.logging_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
