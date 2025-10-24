"""Batch helpers for running the injection phase across multiple files."""

from __future__ import annotations

import logging
from tqdm import tqdm
from pathlib import Path
from typing import Any

from .injector import inject
logger = logging.getLogger(__name__)


def start_injects(
    files: list[str],
    translations: dict,
    output_dir_translated: Path,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Inject translations into a collection of SVG files and write the results."""
    saved_done = 0
    no_save = 0
    nested_files = 0
    no_changes = 0

    files_stats = {}

    for file in tqdm(files, total=len(files), desc="Inject files:"):

        file = Path(str(file))

        tree, stats = inject(
            file,
            all_mappings=translations,
            save_result=False,
            return_stats=True,
            overwrite=overwrite,
        )
        stats["file_path"] = ""

        output_file = output_dir_translated / file.name
        if stats.get("new_languages") == 0:
            no_changes += 1
            files_stats[file.name] = stats
            continue
            
        if not tree:
            logger.debug(f"Failed to translate {file.name}")
            if stats.get("error") == "structure-error-nested-tspans-not-supported":
                nested_files += 1
            else:
                no_save += 1
            files_stats[file.name] = stats
            continue
        try:
            tree.write(str(output_file), encoding='utf-8', xml_declaration=True, pretty_print=True)
            stats["file_path"] = str(output_file)
            saved_done += 1
        except Exception as e:
            logger.error(f"Failed writing {output_file}: {e}")
            stats["error"] = "write-failed"
            stats["file_path"] = ""
            tree = None
            no_save += 1

        files_stats[file.name] = stats

    logger.debug(f"all files: {len(files):,} Saved {saved_done:,}, skipped {no_save:,}, nested_files: {nested_files:,}")

    return {
        "saved_done": saved_done,
        "no_save": no_save,
        "nested_files": nested_files,
        "no_changes": no_changes,
        "files": files_stats,
    }
