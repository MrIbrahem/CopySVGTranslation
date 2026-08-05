"""Injection phase helpers for CopySVGTranslation."""

from .detector import NestedTspanDetector
from .flattener import NestedTspanFlattener

__all__ = [
    "NestedTspanDetector",
    "NestedTspanFlattener",
]
