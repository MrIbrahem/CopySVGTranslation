"""Public API for the CopySVGTranslation package."""

from .extraction import extract
from .injection import generate_unique_id, inject, start_injects
from .text_utils import normalize_text
from .workflows import svg_extract_and_inject, svg_extract_and_injects
from .titles import make_title_translations, get_titles_translations
from .injection import make_translation_ready

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
]
