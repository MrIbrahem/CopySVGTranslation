"""Extraction phase helpers for CopySVGTranslation."""

from pathlib import Path
from typing import Any

from .svg_extractor import SVGTranslationExtractor


def extract(
    svg_file_path: str | Path,
    case_insensitive: bool = True,
) -> dict[str, Any] | None:
    """
    Legacy function-style wrapper around SVGTranslationExtractor, kept for
    backward compatibility with existing callers.

    Parameters:
        svg_file_path (str | Path): Path to the SVG file to process.
        case_insensitive (bool): If true, treat default text keys
            case-insensitively by lowercasing them.

    Returns:
        dict | None: A dictionary containing extracted translations, or
        None if the file does not exist or could not be parsed.
    """
    extractor = SVGTranslationExtractor(
        svg_file_path,
        case_insensitive=case_insensitive,
    )

    result = extractor.extract()
    if result.error:
        return None

    # { "new": {}, "tspans_by_id": {}, "title": { }, "title_new": { } }
    return result.to_json()


__all__ = [
    "extract",
]
