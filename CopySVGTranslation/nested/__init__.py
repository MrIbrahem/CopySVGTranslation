"""Injection phase helpers for CopySVGTranslation."""

from .detector import NestedTspanDetector
from .find_nested import fix_nested_file
from .fixer import MatchFixNestedTags
from .flattener import NestedTspanFlattener

__all__ = [
    "NestedTspanDetector",
    "NestedTspanFlattener",
    "fix_nested_file",
    "MatchFixNestedTags",
]
