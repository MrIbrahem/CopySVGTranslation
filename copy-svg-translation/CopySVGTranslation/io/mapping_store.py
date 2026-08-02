# io/mapping_store.py
from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from pathlib import Path

from ..config import TranslationConfig
from ..core.mapping import TranslationMapping

logger = logging.getLogger(__name__)


class MappingStore:
    """
    Load, merge and save translation mappings as JSON.
    """

    def __init__(self, config: TranslationConfig | None = None) -> None:
        self.config = config or TranslationConfig()

    def load(self, path: Path | str) -> TranslationMapping:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Mapping file not found: {path}")

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        mapping = TranslationMapping.from_any(data)
        logger.debug("Loaded mapping from %s (%d entries)", path, len(mapping.new))
        return mapping

    def load_many(self, paths: Iterable[Path | str]) -> TranslationMapping:
        """Load and merge multiple mapping files."""
        result = TranslationMapping()
        for p in paths:
            try:
                result.merge(self.load(p))
            except FileNotFoundError:
                logger.warning("Mapping file not found, skipped: %s", p)
            except Exception as exc:
                logger.error("Failed to load mapping %s: %s", p, exc)
        return result

    def save(
        self,
        mapping: TranslationMapping,
        path: Path | str,
        *,
        create_parents: bool | None = None,
        indent: int = 2,
    ) -> Path:
        path = Path(path)
        create = self.config.create_parents if create_parents is None else create_parents

        if create:
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                mapping.to_dict(),
                f,
                indent=indent,
                ensure_ascii=False,
            )

        logger.debug("Saved mapping to %s", path)
        return path

    def default_mapping_path(self, svg_path: Path) -> Path:
        """Return the conventional path for a mapping extracted from an SVG."""
        base_dir = self.config.mapping_output_dir or Path.cwd() / "data"
        return base_dir / f"{svg_path.name}.json"
