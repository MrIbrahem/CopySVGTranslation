# legacy/workflows.py
from __future__ import annotations

import warnings
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..config import TranslationConfig
from ..service import SVGTranslationService


def svg_translate_between_files(
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
        "copy_svg_translation.svg_translate_between_files() is deprecated. "
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


def svg_inject_translations(
    *,
    translations: Mapping,
    inject_file: Path | str,
    overwrite: bool | None = None,
    pretty_print: bool | None = None,
    save_result: bool = False,
    target_path: Path | None = None,
) -> Any:
    """
    Deprecated. Use SVGTranslationService.inject() instead.
    """
    warnings.warn(
        "copy_svg_translation.svg_inject_translations() is deprecated. " "Use SVGTranslationService.inject() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    inject_path = Path(str(inject_file))

    from .inject import inject_file_tree

    return inject_file_tree(
        inject_file=inject_path,
        all_mappings=translations,
        save_result=save_result,
        save_path=target_path,
        overwrite=overwrite,
        pretty_print=pretty_print,
    )


__all__ = [
    "svg_translate_between_files",
    "svg_inject_translations",
]
