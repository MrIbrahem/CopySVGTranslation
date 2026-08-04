"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ..config import TranslationConfig
from ..utils.injection_utils import load_all_mappings
from .injector import InjectorData, SVGTranslationInjector

logger = logging.getLogger(__name__)


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
    Legacy function-style wrapper around SVGTranslationInjector, kept for
    backward compatibility with existing callers.
    """
    if not all_mappings and mapping_files:
        mapping_files = list(mapping_files)
        all_mappings = load_all_mappings(mapping_files)

    config = TranslationConfig(
        case_insensitive=case_insensitive,
        overwrite=overwrite,
        pretty_print=pretty_print,
    )
    injector = SVGTranslationInjector(config)

    result: InjectorData = injector.inject(
        inject_file=inject_file,
        all_mappings=all_mappings,
        save_result=save_result,
        save_path=save_path,
    )

    if return_stats:
        return result.tree, result.new_stats.to_json()

    return result.tree


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
