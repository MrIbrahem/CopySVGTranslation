"""Public API for the SvgTanslate package."""

from SvgTanslate.extraction import extract
from SvgTanslate.injection import generate_unique_id, inject, start_injects
from SvgTanslate.text_utils import normalize_text
from SvgTanslate.workflows import svg_extract_and_inject, svg_extract_and_injects

__all__ = [
    "extract",
    "generate_unique_id",
    "inject",
    "normalize_text",
    "start_injects",
    "svg_extract_and_inject",
    "svg_extract_and_injects",
]
