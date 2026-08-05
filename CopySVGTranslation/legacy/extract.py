"""Extraction phase helpers for CopySVGTranslation."""

from pathlib import Path
from typing import Any

from ..config import TranslationConfig
from ..exceptions import SvgIOError, SvgParseError
from ..extraction.extractor import SVGTranslationExtractor


def extract(
    source_file: str | Path,
    case_insensitive: bool = True,
) -> dict[str, Any] | None:
    """
    Legacy function-style wrapper around SVGTranslationExtractor, kept for
    backward compatibility with existing callers.

    Parameters:
        source_file (str | Path): Path to the SVG file to process.
        case_insensitive (bool): If true, treat default text keys
            case-insensitively by lowercasing them.

    Returns:
        dict | None: A dictionary containing extracted translations, or
        None if the file does not exist or could not be parsed.
    """
    config = TranslationConfig(
        case_insensitive=case_insensitive,
    )
    extractor = SVGTranslationExtractor(config)

    try:
        result = extractor.extract(source_file)
    except (SvgIOError, SvgParseError):
        return None

    if result.error:
        return None

    # { "new": {}, "tspans_by_id": {}, "title_new": { } }
    return result.to_json()


__all__ = [
    "extract",
]
