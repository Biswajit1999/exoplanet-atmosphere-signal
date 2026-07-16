"""Structured logging setup driven by config/logging.yml."""
from __future__ import annotations

import logging
import logging.config
from pathlib import Path

import yaml

_DEFAULT_LOGGING_CONFIG = Path(__file__).resolve().parents[2] / "config" / "logging.yml"
_CONFIGURED = False


def configure_logging(config_path: str | Path | None = None) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    path = Path(config_path) if config_path is not None else _DEFAULT_LOGGING_CONFIG
    if path.is_file():
        with path.open("r", encoding="utf-8") as handle:
            logging.config.dictConfig(yaml.safe_load(handle))
    else:
        logging.basicConfig(level=logging.INFO)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
