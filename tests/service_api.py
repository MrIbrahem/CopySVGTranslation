"""Test helpers for exercising the supported SVGTranslationService facade.

The helpers preserve compact test assertions while routing every workflow through
the current public service API rather than through removed compatibility modules.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from CopySVGTranslation import SVGTranslationService, TranslationConfig, TranslationMapping
from CopySVGTranslation.io.mapping_store import MappingStore


def extract_translations(
    source_file: str | Path,
    *,
    case_insensitive: bool = True,
) -> dict[str, Any] | None:
    """Extract a serializable mapping through the supported service facade."""
    service = SVGTranslationService(TranslationConfig(case_insensitive=case_insensitive))
    result = service.extract(source_file)
    return result.data.to_json() if result.success and result.data is not None else None


def inject_translations(
    *,
    inject_file: Path | str | None = None,
    mapping_files: Iterable[Path | str] | None = None,
    mapping: Mapping[str, Any] | None = None,
    case_insensitive: bool = True,
    save_path: Path | str | None = None,
    overwrite_translations: bool = False,
    save_result: bool = False,
    return_stats: bool = False,
    pretty_print: bool | None = None,
    sort_switches: bool | None = None,
) -> tuple[Any, dict[str, Any] | None] | Any:
    """Inject translations through the supported service facade.

    The return shape is intentionally compact for existing test assertions. It
    exposes the tree and serialized statistics derived from ``OperationResult``
    without reintroducing the removed package-level compatibility API.
    """
    if inject_file is None:
        tree, stats = None, {"error": "No inject file provided"}
    else:
        resolved_mapping: Mapping[str, Any] | None = mapping
        if not resolved_mapping and mapping_files:
            loaded_mapping = MappingStore().load_many(mapping_files)
            if not loaded_mapping.is_empty():
                resolved_mapping = loaded_mapping.to_json()

        if not resolved_mapping:
            tree, stats = None, {"error": "No valid mappings found"}
        else:
            config = TranslationConfig(
                case_insensitive=case_insensitive,
                overwrite_translations=overwrite_translations,
                pretty_print=pretty_print,
                sort_switches=sort_switches,
                auto_save=False,
            )
            result = SVGTranslationService(config).inject(
                svg_path=Path(inject_file),
                mapping=TranslationMapping.from_any(resolved_mapping),
                output=Path(save_path) if save_path is not None else None,
                save=save_result or save_path is not None,
            )
            if result.success and result.data is not None:
                tree = result.data.tree
                stats = result.stats.to_json() if result.stats is not None else None
            else:
                tree, stats = None, {"error": result.error or "injection failed"}

    return (tree, stats) if return_stats else tree
