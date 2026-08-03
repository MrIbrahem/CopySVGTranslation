"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ..utils.injection_utils import load_all_mappings
from .svg_injector import InjectorData, SVGTranslationInjector

logger = logging.getLogger(__name__)


def inject_file_tree(
    inject_file: Path | str | None = None,
    mapping_files: Iterable[Path | str] | None = None,
    all_mappings: Mapping | None = None,
    case_insensitive: bool = True,
    save_path: Path | None = None,
    output_dir: Path | None = None,
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

    inject_path = Path(str(inject_file))
    _save_path: Path | None = None

    if save_result:
        if save_path:
            _save_path = Path(str(save_path))
        elif output_dir:
            _save_path = Path(str(output_dir)) / inject_path.name
        else:
            _save_path = inject_path.parent / "translated" / inject_path.name

    injector = SVGTranslationInjector(
        case_insensitive=case_insensitive,
        overwrite=overwrite,
        pretty_print=pretty_print,
    )

    result: InjectorData = injector.inject(
        inject_file=inject_file,
        all_mappings=all_mappings,
        save_result=save_result,
        save_path=_save_path,
    )

    if return_stats:
        return result.tree, result.new_stats.to_json()

    return result.tree


def inject(
    inject_file: Path | str | None = None,
    mapping_files: Iterable[Path | str] | None = None,
    all_mappings: Mapping | None = None,
    case_insensitive: bool = True,
    save_path: Path | None = None,
    output_dir: Path | None = None,
    overwrite: bool = False,
    save_result: bool = False,
    return_stats: bool = False,
    pretty_print: bool | None = None,
) -> tuple[Any, Any] | Any:
    return inject_file_tree(
        inject_file=inject_file,
        mapping_files=mapping_files,
        all_mappings=all_mappings,
        case_insensitive=case_insensitive,
        save_path=save_path,
        output_dir=output_dir,
        overwrite=overwrite,
        save_result=save_result,
        return_stats=return_stats,
        pretty_print=pretty_print,
    )


__all__ = [
    "inject",
    "inject_file_tree",
]
