# __init__.py
"""
CopySVGTranslation
------------------
Extract translations from SVG files and inject them into others.
"""

from __future__ import annotations

__version__ = "2.0.0"

from .config import TranslationConfig
from .core.mapping import TranslationEntry, TranslationMapping
from .exceptions import (
    ConfigurationError,
    CopySVGTranslationError,
    MappingError,
    SvgIOError,
    SvgNestedTspanError,
    SvgParseError,
    SvgStructureError,
)
from .extraction import SVGTranslationExtractor
from .injection import SvgPreparationPipeline, SVGTranslationInjector
from .io import MappingStore, SvgDocument
from .legacy import extract, inject, svg_extract_and_inject
from .nested import NestedTspanDetector, NestedTspanFlattener
from .result import InjectorStats, OperationResult
from .service import SVGTranslationService
from .titles import YearTitleHandler

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
