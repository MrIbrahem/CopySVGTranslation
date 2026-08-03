# __init__.py
"""
copy_svg_translation
------------------
Extract translations from SVG files and inject them into others.
"""

from __future__ import annotations

__version__ = "2.0.1"

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
from .legacy import extract, inject_file_tree
from .nested import NestedTspanDetector, NestedTspanFlattener
from .result import InjectorStats, OperationResult
from .service import SVGTranslationService
from .titles import YearTitleHandler

__all__ = [
    "ConfigurationError",
    "CopySVGTranslationError",
    "InjectorStats",
    "MappingError",
    "MappingStore",
    "NestedTspanDetector",
    "NestedTspanFlattener",
    "OperationResult",
    "SVGTranslationExtractor",
    "SVGTranslationInjector",
    "SVGTranslationService",
    "SvgDocument",
    "SvgIOError",
    "SvgNestedTspanError",
    "SvgParseError",
    "SvgPreparationPipeline",
    "SvgStructureError",
    "TranslationConfig",
    "TranslationEntry",
    "TranslationMapping",
    "YearTitleHandler",
    "__version__",
    "extract",
    "inject_file_tree",
]
