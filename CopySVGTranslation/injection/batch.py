"""Batch helpers for running the injection phase across multiple files."""

from __future__ import annotations

import logging
import shutil
from tqdm import tqdm
from pathlib import Path
from typing import Any

from .injector import inject
logger = logging.getLogger("CopySVGTranslation")


def start_injects(
    files: list[str],
    translations: dict,
    output_dir_translated: Path,
    overwrite: bool = False,
    output_dir_nested_files: Path | None = None,
) -> dict[str, Any]:
    """Inject translations into a collection of SVG files and write the results."""
    data = {}
    success = 0
    failed = 0
    nested_files = 0
    no_changes = 0

    files_stats = {}
    nested_files_list = {}

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
        if not tree:
            logger.debug(f"Failed to translate {file.name}")
            if stats.get("nested_tspan_error"):
                nested_files += 1
                nested_files_list[file.name] = stats.get("node", "")
                if output_dir_nested_files:
                    # copy file to output_dir_nested_files
                    try:
                        shutil.copy(file, output_dir_nested_files / file.name)
                    except Exception as e:
                        logger.error(f"Failed copying {file} to {output_dir_nested_files}: {e}")
            else:
                failed += 1
                files_stats[file.name] = stats
            continue

        if stats.get("new_languages", 0) == 0 and stats.get("updated_translations", 0) == 0:
            no_changes += 1
            files_stats[file.name] = stats
            continue
        try:
            tree.write(str(output_file), encoding='utf-8', xml_declaration=True, pretty_print=True)
            stats["file_path"] = str(output_file)
            success += 1
        except Exception as e:
            logger.error(f"Failed writing {output_file}: {e}")
            stats["error"] = "write-failed"
            stats["file_path"] = ""
            tree = None
            failed += 1

        files_stats[file.name] = stats

    logger.debug(f"all files: {len(files):,} Saved {success:,}, failed {failed:,}, nested_files: {nested_files:,}")

    if output_dir_nested_files:
        data["output_dir_nested_files"] = str(output_dir_nested_files)

    data.update({
        "success": success,
        "failed": failed,
        "nested_files": nested_files,
        "no_changes": no_changes,
        "nested_files_list": nested_files_list,
        "files": files_stats,
    })
    return data
