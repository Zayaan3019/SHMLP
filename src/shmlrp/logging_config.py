from __future__ import annotations

import logging


def setup_logging(level: str = "INFO") -> logging.Logger:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger("shmlrp")
