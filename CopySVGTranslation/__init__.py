"""Public API for the CopySVGTranslation package."""

from .extraction import extract
from .injection import inject
from .nested_analyze import fix_nested_file, match_nested_tags

__all__ = [
    "extract",
    "inject",
    "match_nested_tags",
    "fix_nested_file",
]
