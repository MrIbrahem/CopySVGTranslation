# legacy/workflows.py
from __future__ import annotations

import warnings
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..config import TranslationConfig
from ..service import SVGTranslationService


def svg_extract_and_inject(
    extract_file: Path | str,
    inject_file: Path | str,
    output_file: Path | None = None,
    data_output_file: Path | None = None,
    overwrite: bool | None = None,
    save_result: bool = False,
) -> Any:
    """
    Deprecated. Use SVGTranslationService.extract_and_inject() instead.
    """
    warnings.warn(
        "CopySVGTranslation.svg_extract_and_inject() is deprecated. "
        "Use SVGTranslationService.extract_and_inject() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    config = TranslationConfig(
        overwrite=bool(overwrite),
        auto_save=False,
    )
    service = SVGTranslationService(config)

    save_mapping: bool | Path | None = False
    if data_output_file is not None:
        save_mapping = Path(data_output_file)
    else:
        save_mapping = True

    result = service.extract_and_inject(
        source=extract_file,
        target=inject_file,
        output=output_file,
        save_mapping=save_mapping,
        save=save_result,
    )

    return result.data


def svg_extract_and_injects(
    translations: Mapping,
    inject_file: Path | str,
    output_dir: Path | None = None,
    save_result: bool = False,
    **kwargs: Any,
) -> Any:
    """
    Deprecated. Use SVGTranslationService.inject() instead.
    """
    warnings.warn(
        "CopySVGTranslation.svg_extract_and_injects() is deprecated. " "Use SVGTranslationService.inject() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    from .inject import inject

    return inject(
        inject_file=inject_file,
        all_mappings=translations,
        output_dir=output_dir,
        save_result=save_result,
        **kwargs,
    )
