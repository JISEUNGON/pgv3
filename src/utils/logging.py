from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def configure_root_logger(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="%(levelname)s [%(name)s] %(message)s")

