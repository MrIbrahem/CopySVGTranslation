"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from pathlib import Path

logger = logging.getLogger(__name__)


def get_target_path(
    output_file: Path | str | None,
    output_dir: Path | str | None,
    inject_path: Path,
) -> Path:
    """
    Determine the filesystem path where the modified SVG should be written.

    If `output_file` is provided, it is used as the target path. Otherwise the path is constructed by combining `output_dir` (if given) or the source file's directory with the source file's name. In all cases the parent directories for the resolved path are created if they do not exist.

    Parameters:
        output_file (Path | str | None): Explicit output file path to use.
        output_dir (Path | str | None): Directory to place the output file when `output_file` is not provided.
        inject_path (Path): Path to the original SVG file; its name is used when constructing a target path.

    Returns:
        Path: The resolved filesystem path for the output SVG file.
    """
    if output_dir:
        output_dir = Path(str(output_dir))

    if output_file:
        target_path = Path(str(output_file))
    else:
        save_dir = output_dir or inject_path.parent
        target_path = save_dir / inject_path.name
    target_path.parent.mkdir(parents=True, exist_ok=True)

    return target_path


def generate_unique_id(base_id: str, lang: str, existing_ids: set[str]) -> str:
    """Generate a unique identifier by appending the language and a counter."""
    new_id = f"{base_id}-{lang}"

    # If the base ID with language is unique, use it
    if new_id not in existing_ids:
        return new_id

    # Otherwise, add numeric suffix until unique
    counter = 1
    while f"{new_id}-{counter}" in existing_ids:
        counter += 1

    return f"{new_id}-{counter}"


def load_all_mappings(mapping_files: Iterable[Path | str]) -> dict:
    """Load and merge translation mapping JSON files into a single dictionary."""
    all_mappings: dict = {}

    for mapping_file in mapping_files:
        mapping_path = Path(str(mapping_file))

        if not mapping_path.exists():
            logger.warning(f"Mapping file not found: {mapping_path}")
            continue

        try:
            with open(mapping_path, "r", encoding="utf-8") as f:
                mappings = json.load(f)
        except Exception as exc:
            logger.error(f"Error loading mapping file {mapping_path}: {exc}")
            continue

        for key, value in mappings.items():
            all_mappings.setdefault(key, {}).update(value)

        logger.debug("Loaded mappings from %s, entries: %s", mapping_path, len(mappings))

    return all_mappings


__all__ = [
    "get_target_path",
    "generate_unique_id",
    "load_all_mappings",
]
