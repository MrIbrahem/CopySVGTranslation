"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from pathlib import Path

logger = logging.getLogger(__name__)


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
    mapping: dict = {}

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
            mapping.setdefault(key, {}).update(value)

        logger.debug("Loaded mappings from %s, entries: %s", mapping_path, len(mappings))

    return mapping


__all__ = [
    "generate_unique_id",
    "load_all_mappings",
]
