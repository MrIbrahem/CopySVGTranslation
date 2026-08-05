"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import warnings
import logging
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ..config import TranslationConfig
from ..core.mapping import TranslationMapping
from ..io.mapping_store import MappingStore
from ..injection.injector import InjectorData, SVGTranslationInjector

logger = logging.getLogger(__name__)


def _inject_file_tree(
    *,
    inject_file: Path | str | None = None,
    mapping_files: Iterable[Path | str] | None = None,
    mapping: Mapping | None = None,
    case_insensitive: bool = True,
    save_path: Path | None = None,
    overwrite: bool = False,
    save_result: bool = False,
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
        return (None, {"error": "No inject file provided"})

    # ---- resolve mapping ----
    if not mapping and mapping_files:
        store = MappingStore()
        mapping = store.load_many(mapping_files).to_json()

    if not mapping:
        return (None, {"error": "No valid mappings found"})

    # ---- resolve output path ----
    inject_path = Path(str(inject_file))

    # ---- call new service ----
    config = TranslationConfig(
        case_insensitive=case_insensitive,
        overwrite=overwrite,
        pretty_print=pretty_print,
        auto_save=False,
    )
    service = SVGTranslationInjector(config)

    mapping_obj = TranslationMapping.from_any(mapping)

    result: InjectorData = service.inject(
        svg_path=inject_path,
        mapping=mapping_obj,
        save_path=save_path,
        save=save_result,
    )

    return result.tree, result.new_stats.to_json()

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
    tree, stats = _inject_file_tree(
        inject_file=inject_file,
        mapping_files=mapping_files,
        mapping=mapping,
        case_insensitive=case_insensitive,
        save_path=save_path,
        overwrite=overwrite,
        save_result=save_result,
        pretty_print=pretty_print,
    )

    if return_stats:
        return tree, stats

    return tree


def inject_file_and_save(
    *,
    inject_file: Path | str | None = None,
    mapping_files: Iterable[Path | str] | None = None,
    mapping: Mapping | None = None,
    case_insensitive: bool = True,
    save_path: Path,
    overwrite: bool = False,
    return_stats: bool = False,
    pretty_print: bool | None = None,
) -> tuple[Any, Any] | Any:

    return inject_file_tree(
        inject_file=inject_file,
        mapping_files=mapping_files,
        mapping=mapping,
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
