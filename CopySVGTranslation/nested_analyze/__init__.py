"""Injection phase helpers for CopySVGTranslation."""

from .find_nested import fix_nested_file, fix_nested_tspans, match_nested_tags

__all__ = [
    "fix_nested_tspans",
    "fix_nested_file",
    "match_nested_tags",
]
