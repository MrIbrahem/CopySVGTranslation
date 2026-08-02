# __init__.py
"""
CopySVGTranslation
------------------
Extract translations from SVG files and inject them into others.
"""

from __future__ import annotations

__version__ = "2.0.0"

from .config import TranslationConfig
from .service import SVGTranslationService

from .result import OperationResult, InjectorStats
from .core.mapping import TranslationMapping, TranslationEntry

from .exceptions import (
    CopySVGTranslationError,
    SvgStructureError,
    SvgNestedTspanError,
    SvgParseError,
    SvgIOError,
    MappingError,
    ConfigurationError,
)

from .extraction import SVGTranslationExtractor
from .injection import SVGTranslationInjector, SvgPreparationPipeline
from .titles import YearTitleHandler
from .nested import NestedTspanDetector, NestedTspanFlattener
from .io import SvgDocument, MappingStore

from .legacy import extract, inject, svg_extract_and_inject

__all__ = [
    "__version__",
    "SVGTranslationService",
    "TranslationConfig",
    "OperationResult",
    "InjectorStats",
    "TranslationMapping",
    "TranslationEntry",
    "CopySVGTranslationError",
    "SvgStructureError",
    "SvgNestedTspanError",
    "SvgParseError",
    "SvgIOError",
    "MappingError",
    "ConfigurationError",
    "SVGTranslationExtractor",
    "SVGTranslationInjector",
    "SvgPreparationPipeline",
    "YearTitleHandler",
    "NestedTspanDetector",
    "NestedTspanFlattener",
    "SvgDocument",
    "MappingStore",
    "extract",
    "inject",
    "svg_extract_and_inject",
]
