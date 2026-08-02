# legacy/inject.py
from __future__ import annotations

import warnings
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ..config import TranslationConfig
from ..core.mapping import TranslationMapping
from ..io.mapping_store import MappingStore
from ..service import SVGTranslationService


def inject(
    inject_file: Path | str | None = None,
    mapping_files: Iterable[Path | str] | None = None,
    all_mappings: Mapping | None = None,
    case_insensitive: bool = True,
    output_file: Path | None = None,
    output_dir: Path | None = None,
    overwrite: bool = False,
    save_result: bool = False,
    return_stats: bool = False,
    **kwargs: Any,
) -> tuple[Any, Any] | Any:
    """
    Deprecated. Use SVGTranslationService.inject() instead.
    """
    warnings.warn(
        "CopySVGTranslation.inject() is deprecated. "
        "Use SVGTranslationService.inject() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    if inject_file is None and kwargs.get("svg_file_path"):
        inject_file = kwargs["svg_file_path"]

    if all_mappings is None and kwargs.get("translations"):
        all_mappings = kwargs["translations"]

    if inject_file is None:
        return (None, {"error": "No inject file provided"}) if return_stats else None

    if all_mappings is None and mapping_files:
        store = MappingStore()
        all_mappings = store.load_many(mapping_files).to_dict()

    if not all_mappings:
        return (None, {"error": "No valid mappings found"}) if return_stats else None

    inject_path = Path(str(inject_file))
    target: Path | None = None
    if save_result:
        if output_file:
            target = Path(output_file)
        elif output_dir:
            target = Path(output_dir) / inject_path.name
        else:
            target = Path.cwd() / "translated" / inject_path.name

    config = TranslationConfig(
        case_insensitive=case_insensitive,
        overwrite=overwrite,
        pretty_print=kwargs.get("pretty_print", True),
        auto_save=False,
    )
    service = SVGTranslationService(config)

    result = service.inject(
        inject_path,
        TranslationMapping.from_any(all_mappings),
        output=target,
        save=save_result,
    )

    if return_stats:
        stats = result.stats.to_json() if result.stats else {}
        if not result.success:
            stats["error"] = result.error or "injection_failed"
        return result.data, stats

    return result.data
