"""High-level workflows that combine the extraction and injection phases."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Mapping

from .extraction import extract
from .injection import inject

logger = logging.getLogger("CopySVGTranslation")


def svg_extract_and_inject(
    extract_file: Path | str,
    inject_file: Path | str,
    output_file: Path | None = None,
    data_output_file: Path | None = None,
    overwrite: bool | None = None,
    save_result: bool = False,
):
    """
    Extract translations from one SVG and inject them into another.

    Parameters:
        extract_file (Path | str): Path to the SVG file to extract translations from.
        inject_file (Path | str): Path to the SVG file to inject translations into.
        output_file (Path | None): Optional path for the resulting injected SVG. If omitted, a file with the same name as `inject_file` is created in a `translated` directory under the current working directory.
        data_output_file (Path | None): Optional path for the JSON file that will store extracted translations. If omitted, a file named after `extract_file` is created in a `data` directory under the current working directory.
        overwrite (bool | None): If `True`, existing translation nodes inside the SVG are updated; when `False`, they are left as-is. Ignored for file I/O: when `save_result=True`, the output file is written regardless. `None` is treated as `False`.
        save_result (bool): If `True`, the injection result will be saved to `output_file`.

    Returns:
        ElementTree | None: The parsed tree of the injected SVG when successful, `None` if extraction or injection failed.
    """
    extract_path = Path(str(extract_file))
    inject_path = Path(str(inject_file))

    translations = extract(extract_path, case_insensitive=True)
    if not translations:
        logger.error(f"Failed to extract translations from {extract_path}")
        return None

    if not data_output_file:
        json_output_dir = Path.cwd() / "data"
        json_output_dir.mkdir(parents=True, exist_ok=True)

        data_output_file = json_output_dir / f"{extract_path.name}.json"

    data_output_file = Path(str(data_output_file))
    data_output_file.parent.mkdir(parents=True, exist_ok=True)

    # Save translations to JSON
    with open(data_output_file, 'w', encoding='utf-8') as handle:
        json.dump(translations, handle, indent=2, ensure_ascii=False)

    logger.debug(f"Saved translations to {data_output_file}")

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
        logger.error(f"Failed to inject translations into {inject_path}")
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
        inject_file=inject_path,
        all_mappings=translations,
        output_dir=output_dir,
        save_result=save_result,
        **kwargs,
    )
