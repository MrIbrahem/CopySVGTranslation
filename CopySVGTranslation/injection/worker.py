"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ..utils.injection_utils import get_target_path, load_all_mappings
from .svg_injector import InjectorData, SVGTranslationInjector

logger = logging.getLogger(__name__)


def inject(
    inject_file: Path | str | None = None,
    mapping_files: Iterable[Path | str] | None = None,
    all_mappings: Mapping | None = None,
    case_insensitive: bool = True,
    output_file: Path | None = None,
    output_dir: Path | None = None,
    overwrite: bool = False,
    save_result: bool = False,
    return_stats: bool = False,
    **kwargs: Any,
) -> tuple[Any, Any] | Any:
    """
    Legacy function-style wrapper around SVGTranslationInjector, kept for
    backward compatibility with existing callers.
    """
    if not inject_file and kwargs.get("svg_file_path"):
        inject_file = kwargs["svg_file_path"]

    if not all_mappings and kwargs.get("translations"):
        all_mappings = kwargs["translations"]

    if not all_mappings and mapping_files:
        mapping_files = list(mapping_files)
        all_mappings = load_all_mappings(mapping_files)

    pretty_print = kwargs.get("pretty_print", True)

    inject_path = Path(str(inject_file))
    target_path = get_target_path(output_file, output_dir, inject_path) if save_result else None

    injector = SVGTranslationInjector(
        case_insensitive=case_insensitive,
        overwrite=overwrite,
        pretty_print=pretty_print,
    )

    result: InjectorData = injector.inject(
        inject_file,
        all_mappings=all_mappings,
        save_result=save_result,
        target_path=target_path,
    )

    if return_stats:
        return result.tree, result.new_stats.to_json()

    return result.tree


__all__ = [
    "inject",
]
