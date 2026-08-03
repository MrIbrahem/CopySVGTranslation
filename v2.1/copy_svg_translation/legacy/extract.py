# legacy/extract.py
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

from ..config import TranslationConfig
from ..service import SVGTranslationService


def extract(
    source_file: str | Path,
    case_insensitive: bool = True,
) -> dict[str, Any] | None:
    """
    Deprecated. Use SVGTranslationService.extract() instead.

    Legacy function-style wrapper kept for backward compatibility.
    Returns a plain dict (or None on failure), matching the old API.
    """
    warnings.warn(
        "copy_svg_translation.extract() is deprecated. Use SVGTranslationService.extract() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    config = TranslationConfig(case_insensitive=case_insensitive)
    service = SVGTranslationService(config)
    result = service.extract(source_file)

    if not result.success or result.data is None:
        return None

    return result.data.to_dict()
