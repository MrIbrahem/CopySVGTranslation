"""Public API for the SvgTranslate package."""

from SvgTranslate.extraction import extract
from SvgTranslate.injection import generate_unique_id, inject, start_injects
from SvgTranslate.text_utils import normalize_text
from SvgTranslate.workflows import svg_extract_and_inject, svg_extract_and_injects

__all__ = [
    "extract",
    "generate_unique_id",
    "inject",
    "normalize_text",
    "start_injects",
    "svg_extract_and_inject",
    "svg_extract_and_injects",
]
