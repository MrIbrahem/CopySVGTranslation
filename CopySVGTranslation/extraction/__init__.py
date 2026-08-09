"""Extraction phase helpers for CopySVGTranslation."""

from .extractor import SVGTranslationExtractor
from .header import HeaderMappingExtractor
from .strategies import (
    ByPositionStrategy,
    ByTspanIdStrategy,
    CompositeMatchingStrategy,
    MatchingStrategy,
)
from .switch_collector import SwitchTranslationCollector

__all__ = [
    "ByPositionStrategy",
    "ByTspanIdStrategy",
    "CompositeMatchingStrategy",
    "HeaderMappingExtractor",
    "MatchingStrategy",
    "SVGTranslationExtractor",
    "SwitchTranslationCollector",
]
