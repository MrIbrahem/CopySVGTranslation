"""Injection phase helpers for CopySVGTranslation."""

from .detector import NestedTspanDetector
from .fixer import MatchFixNestedTags
from .flattener import NestedTspanFlattener

__all__ = [
    "NestedTspanDetector",
    "NestedTspanFlattener",
    "MatchFixNestedTags",
]
