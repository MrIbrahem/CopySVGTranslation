from __future__ import annotations

import logging
from pathlib import Path

from .detector import NestedTspanDetector
logger = logging.getLogger(__name__)

def match_nested_tags(source_file: Path) -> list:
    detector = NestedTspanDetector()
    return detector.find_in_file(source_file)

__all__ = [
    "match_nested_tags",
]
