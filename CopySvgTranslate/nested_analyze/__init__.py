"""Injection phase helpers for CopySvgTranslate."""

from .find_nested import match_nested_tags, fix_nested_file, fix_nested_tspans
from .batch import analyze_nested_tags

__all__ = [
    "fix_nested_tspans",
    "analyze_nested_tags",
    "fix_nested_file",
    "match_nested_tags",
]
