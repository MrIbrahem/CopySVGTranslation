# __init__.py
"""
copy_svg_translation
------------------
Extract translations from SVG files and inject them into others.

Modern entry point:
    from copy_svg_translation import SVGTranslationService, TranslationConfig

Legacy functions (deprecated):
    from copy_svg_translation import extract, inject_file_tree
"""

from __future__ import annotations

__version__ = "2.0.1"

# ---------------------------------------------------------------------------
# Primary public API
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Optional advanced exports (still public, but less commonly needed)
# ---------------------------------------------------------------------------
from .extraction import SVGTranslationExtractor
from .injection import SVGTranslationInjector
from .io import MappingStore, SvgDocument

# ---------------------------------------------------------------------------
# Legacy compatibility layer (deprecated)
# ---------------------------------------------------------------------------
from .legacy import extract, inject_file_tree
from .nested import MatchFixNestedTags, NestedTspanDetector, NestedTspanFlattener
from .preparation import SvgPreparationPipeline
from .result import InjectorStats, OperationResult
from .service import SVGTranslationService
from .titles import YearTitleHandler

__all__ = [
    # version
    "__version__",
    "ConfigurationError",
    "CopySVGTranslationError",
    "InjectorStats",
    "MappingError",
    "MappingStore",
    "MatchFixNestedTags",
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
