"""Public API for the svg_translate package."""

from svg_translate.extraction import extract
from svg_translate.injection import generate_unique_id, inject, start_injects
from svg_translate.text_utils import normalize_text
from svg_translate.workflows import svg_extract_and_inject, svg_extract_and_injects

__all__ = [
    "extract",
    "generate_unique_id",
    "inject",
    "normalize_text",
    "start_injects",
    "svg_extract_and_inject",
    "svg_extract_and_injects",
]
