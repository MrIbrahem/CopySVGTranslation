"""High-level workflows that combine the extraction and injection phases."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Mapping

from .extraction import extract
from .injection import inject

logger = logging.getLogger(__name__)


def svg_extract_and_inject(
    extract_file: Path | str,
    inject_file: Path | str,
    output_file: Path | None = None,
    data_output_file: Path | None = None,
    overwrite: bool | None = None,
    save_result: bool = False,
):
    """Extract translations from one SVG and inject them into another."""
    extract_path = Path(str(extract_file))
    inject_path = Path(str(inject_file))

    translations = extract(extract_path, case_insensitive=True)
    if not translations:
        logger.error("Failed to extract translations from %s", extract_path)
        return None

    if not data_output_file:
        json_output_dir = Path.cwd() / "data"
        json_output_dir.mkdir(parents=True, exist_ok=True)
        data_output_file = json_output_dir / f"{extract_path.name}.json"

    with open(data_output_file, 'w', encoding='utf-8') as handle:
        json.dump(translations, handle, indent=2, ensure_ascii=False)
    logger.debug("Saved translations to %s", data_output_file)

    if not output_file:
        output_dir = Path.cwd() / "translated"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / inject_path.name

    tree, stats = inject(
        inject_path,
        mapping_files=[data_output_file],
        output_file=output_file,
        overwrite=bool(overwrite),
        save_result=save_result,
        return_stats=True,
    )

    if tree is None:
        logger.error("Failed to inject translations into %s", inject_path)
    else:
        logger.debug("Injection stats: %s", stats)

    return tree


def svg_extract_and_injects(
    translations: Mapping,
    inject_file: Path | str,
    output_dir: Path | None = None,
    save_result: bool = False,
    **kwargs,
):
    """Inject provided translations into a single SVG file."""
    inject_path = Path(str(inject_file))

    if not output_dir and save_result:
        output_dir = Path.cwd() / "translated"
        output_dir.mkdir(parents=True, exist_ok=True)

    return inject(
        inject_path,
        output_dir=output_dir,
        all_mappings=translations,
        save_result=save_result,
        **kwargs,
    )
