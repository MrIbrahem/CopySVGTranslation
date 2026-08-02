"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from pathlib import Path

from ..utils.injection_utils import load_all_mappings
from .svg_injector import SVGTranslationInjector

logger = logging.getLogger(__name__)


def inject(
    inject_file: Path | str,
    mapping_files: Iterable[Path | str] | None = None,
    all_mappings: Mapping | None = None,
    case_insensitive: bool = True,
    output_file: Path | None = None,
    output_dir: Path | None = None,
    overwrite: bool = False,
    save_result: bool = False,
    return_stats: bool = False,
    **kwargs,
):
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

    injector = SVGTranslationInjector(
        case_insensitive=case_insensitive,
        overwrite=overwrite,
        pretty_print=pretty_print,
    )

    return injector.inject(
        inject_file,
        all_mappings=all_mappings,
        output_file=output_file,
        output_dir=output_dir,
        save_result=save_result,
        return_stats=return_stats,
    )


__all__ = [
    "inject",
]
