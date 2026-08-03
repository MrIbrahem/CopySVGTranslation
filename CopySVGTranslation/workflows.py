"""High-level workflows that combine the extraction and injection phases."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .extraction import extract
from .injection import InjectorData, SVGTranslationInjector, inject_file_tree
from .utils import load_all_mappings

logger = logging.getLogger(__name__)


def svg_extract_and_inject(
    extract_file: Path | str,
    inject_file: Path | str,
    target_path: Path | None = None,
    all_mappings_file: Path | None = None,
    overwrite: bool | None = None,
    save_result: bool = False,
    pretty_print: bool | None = None,
) -> Any:
    """
    Extract translations from one SVG and inject them into another.

    Parameters:
        extract_file (Path | str): Path to the SVG file to extract translations from.
        inject_file (Path | str): Path to the SVG file to inject translations into.
        target_path (Path | None): Optional path for the resulting injected SVG. If omitted, a file with the same name as `inject_file` is created in a `translated` directory under the current working directory.
        all_mappings_file (Path | None): Optional path for the JSON file that will store extracted translations. If omitted, a file named after `extract_file` is created in a `data` directory under the current working directory.
        overwrite (bool | None): If `True`, existing translation nodes inside the SVG are updated; when `False`, they are left as-is. Ignored for file I/O: when `save_result=True`, the output file is written regardless. `None` is treated as `False`.
        save_result (bool): If `True`, the injection result will be saved to `target_path`.

    Returns:
        ElementTree | None: The parsed tree of the injected SVG when successful, `None` if extraction or injection failed.
    """
    extract_path = Path(str(extract_file))
    inject_path = Path(str(inject_file))
    _target_path = target_path

    translations = extract(extract_path, case_insensitive=True)
    all_mappings = translations

    if not all_mappings and all_mappings_file:
        all_mappings = load_all_mappings([all_mappings_file])

    if not all_mappings:
        logger.error(f"Failed to extract translations from {extract_path}")
        return None

    if not _target_path:
        output_dir = inject_path.parent / "translated"
        output_dir.mkdir(parents=True, exist_ok=True)
        _target_path = output_dir / inject_path.name

    tree, stats = inject_file_tree(
        inject_path,
        all_mappings=all_mappings,
        save_path=_target_path,
        overwrite=bool(overwrite),
        save_result=save_result,
        pretty_print=pretty_print,
        return_stats=True,
    )

    if tree is None:
        logger.error(f"Failed to inject translations into {inject_path}")
    else:
        logger.debug("Injection stats: %s", stats)

    return tree


def svg_extract_and_injects(
    translations: Mapping,
    inject_file: Path | str,
    output_dir: Path | None = None,
    save_result: bool = False,
    overwrite: bool | None = None,
    pretty_print: bool | None = None,
) -> Any:
    """
    Inject provided translations into a single SVG file.
    """
    inject_path = Path(str(inject_file))
    _target_path: Path | None = None

    if save_result:
        if output_dir:
            _target_path = Path(str(output_dir)) / inject_path.name
        else:
            _target_path = inject_path.parent / "translated" / inject_path.name

    injector = SVGTranslationInjector(
        case_insensitive=True,
        overwrite=overwrite,
        pretty_print=pretty_print,
    )

    data: InjectorData = injector.inject(
        inject_file=inject_path,
        all_mappings=translations,
        save_result=save_result,
        save_path=_target_path,
    )

    # stats = data.new_stats.to_json()

    return data.tree


__all__ = [
    "svg_extract_and_inject",
    "svg_extract_and_injects",
]
