# extraction/__init__.py
from .extractor import SVGTranslationExtractor
from .strategies import (
    MatchingStrategy,
    ByTspanIdStrategy,
    ByPositionStrategy,
    CompositeMatchingStrategy,
)

__all__ = [
    "SVGTranslationExtractor",
    "MatchingStrategy",
    "ByTspanIdStrategy",
    "ByPositionStrategy",
    "CompositeMatchingStrategy",
]
