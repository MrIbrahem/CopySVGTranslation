"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import logging
import warnings
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ..config import TranslationConfig
from ..core.mapping import TranslationMapping
from ..io.mapping_store import MappingStore
from ..service import SVGTranslationService

logger = logging.getLogger(__name__)


def inject_file_tree(
    *,
    inject_file: Path | str | None = None,
    mapping_files: Iterable[Path | str] | None = None,
    mapping: Mapping | None = None,
    case_insensitive: bool = True,
    save_path: Path | None = None,
    overwrite: bool = False,
    save_result: bool = False,
    return_stats: bool = False,
    pretty_print: bool | None = None,
) -> tuple[Any, Any] | Any:
    """
    Deprecated. Use SVGTranslationService.inject() instead.
    """
    warnings.warn(
        "copy_svg_translation.inject() is deprecated. Use SVGTranslationService.inject() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    # ---- normalize legacy argument aliases ----

    if inject_file is None:
        return (None, {"error": "No inject file provided"}) if return_stats else None

    # ---- resolve mapping ----
    if mapping is None and mapping_files:
        store = MappingStore()
        mapping = store.load_many(mapping_files).to_json()

    if not mapping:
        return (None, {"error": "No valid mappings found"}) if return_stats else None

    # ---- resolve output path ----
    inject_path = Path(str(inject_file))

    # ---- call new service ----
    config = TranslationConfig(
        case_insensitive=case_insensitive,
        overwrite=overwrite,
        pretty_print=pretty_print,
        auto_save=False,
    )
    service = SVGTranslationService(config)

    mapping_obj = TranslationMapping.from_any(mapping)

    result = service.inject(
        svg_path=inject_path,
        mapping=mapping_obj,
        output=save_path,
        save=save_result,
    )

    if return_stats:
        stats = result.stats.to_json() if result.stats else {}
        if not result.success:
            stats["error"] = result.error or "injection_failed"
        return result.data, stats

    return result.data

__all__ = [
    "inject_file_tree",
]
