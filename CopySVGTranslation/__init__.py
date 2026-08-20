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

from .config import TranslationConfig
from .core.mapping import TranslationEntry, TranslationMapping

# ---------------------------------------------------------------------------
# Primary public API
# ---------------------------------------------------------------------------
from .exceptions import CopySVGTranslationError

# ---------------------------------------------------------------------------
# Optional advanced exports (still public, but less commonly needed)
# ---------------------------------------------------------------------------
from .extraction import SVGTranslationExtractor
from .injection import SVGTranslationInjector

# ---------------------------------------------------------------------------
# Legacy compatibility layer (deprecated)
# ---------------------------------------------------------------------------
from .nested import (
    NestedTspanDetector,
    NestedTspanFlattener,
)
from .service import SVGTranslationService

__all__ = [
    # version
    "__version__",
    "CopySVGTranslationError",
    "NestedTspanDetector",
    "NestedTspanFlattener",
    "SVGTranslationExtractor",
    "SVGTranslationInjector",
    "SVGTranslationService",
    "TranslationConfig",
    "TranslationEntry",
    "TranslationMapping",
]
