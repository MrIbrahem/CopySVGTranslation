"""High-level workflows that combine the extraction and injection phases."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .extraction import extract
from .injection import InjectorData, SVGTranslationInjector
from .utils import load_all_mappings

logger = logging.getLogger(__name__)


def svg_translate_between_files(
    *,
    extract_file: Path | str,
    inject_file: Path | str,
    all_mappings_file: Path | None = None,
    overwrite: bool | None = None,
    pretty_print: bool | None = None,
    save_result: bool = False,
    target_path: Path | None = None,
) -> Any:
    """
    Extract translations from one SVG and inject them into another.

    Parameters:
        extract_file (Path | str): Path to the SVG file to extract translations from.
        inject_file (Path | str): Path to the SVG file to inject translations into.
        target_path (Path): path for the resulting injected SVG.
        all_mappings_file (Path | None): Optional path for the JSON file that will store extracted translations. If omitted, a file named after `extract_file` is created in a `data` directory under the current working directory.
        overwrite (bool | None): If `True`, existing translation nodes inside the SVG are updated; when `False`, they are left as-is. Ignored for file I/O: when `save_result=True`, the output file is written regardless. `None` is treated as `False`.
        save_result (bool): If `True`, the injection result will be saved to `target_path`.

    Returns:
        ElementTree | None: The parsed tree of the injected SVG when successful, `None` if extraction or injection failed.
    """
    extract_path = Path(str(extract_file))
    inject_path = Path(str(inject_file))

    translations = extract(extract_path, case_insensitive=True)
    all_mappings = translations

    if not all_mappings and all_mappings_file:
        all_mappings = load_all_mappings([all_mappings_file])

    if not all_mappings:
        logger.error(f"Failed to extract translations from {extract_path}")
        return None

    injector = SVGTranslationInjector(
        case_insensitive=True,
        overwrite=overwrite,
        pretty_print=pretty_print,
    )

    result: InjectorData = injector.inject(
        inject_file=inject_path,
        all_mappings=all_mappings,
        save_result=save_result,
        save_path=target_path,
    )

    if result.tree is None:
        logger.error(f"Failed to inject translations into {inject_path}")
    else:
        stats = result.new_stats.to_json()
        logger.debug("Injection stats: %s", stats)

    return result.tree


def svg_inject_translations(
    *,
    translations: Mapping,
    inject_file: Path | str,
    overwrite: bool | None = None,
    pretty_print: bool | None = None,
    save_result: bool = False,
    target_path: Path | None = None,
) -> Any:
    """
    Inject provided translations into a single SVG file.
    """
    inject_path = Path(str(inject_file))

    injector = SVGTranslationInjector(
        case_insensitive=True,
        overwrite=overwrite,
        pretty_print=pretty_print,
    )

    data: InjectorData = injector.inject(
        inject_file=inject_path,
        all_mappings=translations,
        save_result=save_result,
        save_path=target_path,
    )

    # stats = data.new_stats.to_json()

    return data.tree


__all__ = [
    "svg_translate_between_files",
    "svg_inject_translations",
]
