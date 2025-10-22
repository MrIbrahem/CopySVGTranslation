"""Public API for the CopySvgTranslate package."""

from .extraction import extract
from .injection import generate_unique_id, inject, start_injects
from .text_utils import normalize_text
from .workflows import svg_extract_and_inject, svg_extract_and_injects

__all__ = [
    "extract",
    "generate_unique_id",
    "inject",
    "normalize_text",
    "start_injects",
    "svg_extract_and_inject",
    "svg_extract_and_injects",
]
