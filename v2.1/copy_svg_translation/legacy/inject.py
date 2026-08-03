"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import warnings
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ..config import TranslationConfig
from ..core.mapping import TranslationMapping
from ..io.mapping_store import MappingStore
from ..service import SVGTranslationService


def inject_file_tree(
    *,
    inject_file: Path | str | None = None,
    mapping_files: Iterable[Path | str] | None = None,
    all_mappings: Mapping | None = None,
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
    if all_mappings is None and mapping_files:
        store = MappingStore()
        all_mappings = store.load_many(mapping_files).to_dict()

    if not all_mappings:
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

    result = service.inject(
        inject_path,
        TranslationMapping.from_any(all_mappings),
        output=save_path,
        save=save_result,
    )

    if return_stats:
        stats = result.stats.to_json() if result.stats else {}
        if not result.success:
            stats["error"] = result.error or "injection_failed"
        return result.data, stats

    return result.data


def inject_file_and_save(
    *,
    inject_file: Path | str | None = None,
    mapping_files: Iterable[Path | str] | None = None,
    all_mappings: Mapping | None = None,
    case_insensitive: bool = True,
    save_path: Path,
    overwrite: bool = False,
    return_stats: bool = False,
    pretty_print: bool | None = None,
) -> tuple[Any, Any] | Any:

    return inject_file_tree(
        inject_file=inject_file,
        mapping_files=mapping_files,
        all_mappings=all_mappings,
        case_insensitive=case_insensitive,
        overwrite=overwrite,
        pretty_print=pretty_print,
        save_path=save_path,
        save_result=True,
        return_stats=return_stats,
    )


__all__ = [
    "inject_file_and_save",
    "inject_file_tree",
]
