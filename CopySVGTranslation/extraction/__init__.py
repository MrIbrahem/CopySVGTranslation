"""Extraction phase helpers for CopySVGTranslation."""

from .extractor import SVGTranslationExtractor
from .strategies import (
    ByPositionStrategy,
    ByTspanIdStrategy,
    CompositeMatchingStrategy,
    MatchingStrategy,
)
from .worker import extract

__all__ = [
    "ByPositionStrategy",
    "ByTspanIdStrategy",
    "CompositeMatchingStrategy",
    "MatchingStrategy",
    "SVGTranslationExtractor",
    "extract",
]
