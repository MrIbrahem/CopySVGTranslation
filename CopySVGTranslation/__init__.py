"""Public API for the CopySVGTranslation package."""

from .extraction import extract
from .injection import generate_unique_id, inject, make_translation_ready, start_injects
from .nested_analyze import fix_nested_file, fix_nested_tspans, match_nested_tags
from .text_utils import normalize_text
from .titles import get_titles_translations, make_title_translations
from .workflows import svg_extract_and_inject, svg_extract_and_injects

__all__ = [
    "extract",
    "generate_unique_id",
    "inject",
    "normalize_text",
    "start_injects",
    "svg_extract_and_inject",
    "svg_extract_and_injects",
    "make_title_translations",
    "get_titles_translations",
    "make_translation_ready",
    "match_nested_tags",
    "fix_nested_tspans",
    "fix_nested_file",
]
