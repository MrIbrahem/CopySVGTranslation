"""Batch helpers for running the injection phase across multiple files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, Sequence

from .injector import inject

logger = logging.getLogger(__name__)


def start_injects(
    files: Iterable[Path | str] | Sequence[Path | str],
    translations: dict,
    output_dir_translated: Path,
    overwrite: bool = False,
):
    """Inject translations into a collection of SVG files and write the results."""
    saved_done = 0
    no_save = 0
    nested_files = 0

    files_stats = {}

    if isinstance(files, Sequence):
        iterable = enumerate(files, 1)
        expected_total = len(files)
    else:
        iterable = enumerate(files, 1)
        expected_total = None

    processed = 0

    for processed, file in iterable:
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

        if not tree:
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
        except Exception as exc:  # noqa: BLE001 - broad but logged
            logger.error("Failed writing %s: %s", output_file, exc)
            stats["error"] = "write-failed"
            stats["file_path"] = ""
            tree = None
            no_save += 1

        files_stats[file.name] = stats

    total = expected_total if expected_total is not None else processed

    logger.debug(
        "all files: %s Saved %s, skipped %s, nested_files: %s",
        total,
        saved_done,
        no_save,
        nested_files,
    )

    return {
        "saved_done": saved_done,
        "no_save": no_save,
        "nested_files": nested_files,
        "files": files_stats,
    }
