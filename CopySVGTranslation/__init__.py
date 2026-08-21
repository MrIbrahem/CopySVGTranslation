"""
Public API for the CopySVGTranslation package.

Use :class:`SVGTranslationService` for SVG translation workflows and
:class:`TranslationConfig` to configure them.
"""

from __future__ import annotations

from .config import TranslationConfig
from .core.mapping import TranslationEntry, TranslationMapping
from .exceptions import CopySVGTranslationError
from .nested import (
    NestedStructureService,
    NestedTspanDetector,
    NestedTspanFlattener,
    RepairResult,
)
from .service import SVGTranslationService

__all__ = [
    "CopySVGTranslationError",
    "NestedTspanDetector",
    "NestedTspanFlattener",
    "NestedStructureService",
    "RepairResult",
    "SVGTranslationService",
    "TranslationConfig",
    "TranslationEntry",
    "TranslationMapping",
]
