"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from pathlib import Path

logger = logging.getLogger(__name__)

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
