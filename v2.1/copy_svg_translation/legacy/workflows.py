# legacy/workflows.py
from __future__ import annotations

import warnings
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..config import TranslationConfig
from ..service import SVGTranslationService


def svg_extract_and_inject(
    *,
    extract_file: Path | str,
    inject_file: Path | str,
    all_mappings_file: Path | None = None,
    overwrite: bool | None = None,
    pretty_print: bool | None = None,
    save_result: bool = False,
    target_path: Path | None = None,
) -> Any:
    """
    Deprecated. Use SVGTranslationService.extract_and_inject() instead.
    """
    warnings.warn(
        "copy_svg_translation.svg_extract_and_inject() is deprecated. "
        "Use SVGTranslationService.extract_and_inject() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    config = TranslationConfig(
        overwrite=bool(overwrite),
        pretty_print=pretty_print,
        auto_save=False,
    )

    service = SVGTranslationService(config)

    save_mapping: bool | Path | None = False
    save_mapping = Path(all_mappings_file) if all_mappings_file is not None else True

    result = service.extract_and_inject(
        source=extract_file,
        target=inject_file,
        output=target_path,
        save_mapping=save_mapping,
        save=save_result,
    )

    return result.data


def svg_extract_and_injects(
    *,
    translations: Mapping,
    inject_file: Path | str,
    output_dir: Path | None = None,
    overwrite: bool | None = None,
    pretty_print: bool | None = None,
    save_result: bool = False,
    target_path: Path | None = None,
) -> Any:
    """
    Deprecated. Use SVGTranslationService.inject() instead.
    """
    warnings.warn(
        "copy_svg_translation.svg_extract_and_injects() is deprecated. " "Use SVGTranslationService.inject() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    inject_path = Path(str(inject_file))
    _target_path: Path | None = target_path

    if save_result and not _target_path:
        if output_dir:
            _target_path = Path(str(output_dir)) / inject_path.name
        else:
            _target_path = inject_path.parent / "translated" / inject_path.name

    from .inject import inject_file_tree

    return inject_file_tree(
        inject_file=inject_path,
        all_mappings=translations,
        save_result=save_result,
        save_path=_target_path,
        overwrite=overwrite,
        pretty_print=pretty_print,
    )


__all__ = [
    "svg_extract_and_inject",
    "svg_extract_and_injects",
]
