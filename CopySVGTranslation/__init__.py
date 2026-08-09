"""
Public API for the CopySVGTranslation package.
------------------
Extract translations from SVG files and inject them into others.


Used in copy-svg-langs project:
from CopySVGTranslation import SVGTranslationExtractor, TranslationConfig
from CopySVGTranslation import TranslationMapping, SVGTranslationInjector
from CopySVGTranslation import NestedTspanDetector, NestedTspanFlattener
"""

from __future__ import annotations

__version__ = "0.2.3"

# ---------------------------------------------------------------------------
# Primary public API
# ---------------------------------------------------------------------------
from .config import TranslationConfig
from .core.mapping import TranslationEntry, TranslationMapping

# ---------------------------------------------------------------------------
# Optional advanced exports (still public, but less commonly needed)
# ---------------------------------------------------------------------------
from .extraction import SVGTranslationExtractor
from .injection import SVGTranslationInjector

# ---------------------------------------------------------------------------
# Legacy compatibility layer (deprecated)
# ---------------------------------------------------------------------------
from .nested import (
    MatchFixNestedTags,
    NestedTspanDetector,
    NestedTspanFlattener,
    NestedStructureService,
    RepairResult,
)
from .service import SVGTranslationService

__all__ = [
    # version
    "__version__",
    "MatchFixNestedTags",
    "NestedTspanDetector",
    "NestedTspanFlattener",
    "NestedStructureService",
    "RepairResult",
    "SVGTranslationExtractor",
    "SVGTranslationInjector",
    "SVGTranslationService",
    "TranslationConfig",
    "TranslationEntry",
    "TranslationMapping",
]
