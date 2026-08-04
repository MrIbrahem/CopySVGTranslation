"""Injection phase helpers for CopySVGTranslation."""

from .find_nested import fix_nested_file
from .match_tags import match_nested_tags

from .detector import NestedTspanDetector
from .flattener import NestedTspanFlattener

__all__ = [
    "NestedTspanDetector",
    "NestedTspanFlattener",
    "fix_nested_file",
    "match_nested_tags",
]
