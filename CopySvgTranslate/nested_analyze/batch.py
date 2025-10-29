"""Batch helpers for running the injection phase across multiple files."""

from __future__ import annotations

import json
import logging
from tqdm import tqdm
from pathlib import Path
from typing import Any
from .find_nested import match_nested_tags, fix_nested_file

logger = logging.getLogger("CopySvgTranslate")


def analyze_nested_tags(
    files: list[str]
) -> dict[str, Any]:
    """
    !
    """
    data = {
        "all_files": len(files),
        "status": {
            "len_nested_files": 0,
            "fixed": 0,
            "not_fixed": 0,
        },
        "len_nested_tags_before": {0: 0},
        "len_nested_tags_after": {0: 0},
    }
    nested_data = {}
    nested_files = 0
    fixed = 0
    not_fixed = 0

    for file in tqdm(files, total=len(files), desc="analyze_nested_tags:"):
        file_path = Path(str(file))

        nested_tags = match_nested_tags(file_path)
        if not nested_tags:
            continue

        nested_files += 1
        len_nested = len(nested_tags)
        # ---
        data["len_nested_tags_before"].setdefault(len_nested, 0)
        data["len_nested_tags_before"][len_nested] += 1
        # ---
        if len_nested > 10 :
            # ---
            data["len_nested_tags_after"].setdefault(len_nested, 0)
            data["len_nested_tags_after"][len_nested] += 1
            # ---
            data["nested_files_list"].append(file)
            nested_data[file] = nested_tags
            not_fixed += 1
            continue

        file_fixed = fix_nested_file(file_path, file_path)

        if file_fixed:
            nested_tags = match_nested_tags(file_fixed)
            len_nested = len(nested_tags)
            if not nested_tags:
                fixed += 1
                # ---
                data["len_nested_tags_after"][0] += 1
                # ---
                continue

        data["len_nested_tags_after"].setdefault(len_nested, 0)
        data["len_nested_tags_after"][len_nested] += 1
        # ---
        nested_data[file] = nested_tags
        # ---
        not_fixed += 1

    logger.debug(f"analyze_nested_tags files: {len(files):,} nested: {nested_files:,} fixed {fixed:,}, not_fixed {not_fixed:,}")

    data["status"] = {
        "len_nested_files": nested_files,
        "fixed": fixed,
        "not_fixed": not_fixed,
    }

    return data
