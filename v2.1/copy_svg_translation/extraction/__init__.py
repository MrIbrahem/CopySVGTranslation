# extraction/__init__.py
from .extractor import SVGTranslationExtractor
from .strategies import (
    ByPositionStrategy,
    ByTspanIdStrategy,
    CompositeMatchingStrategy,
    MatchingStrategy,
)

__all__ = [
    "ByPositionStrategy",
    "ByTspanIdStrategy",
    "CompositeMatchingStrategy",
    "MatchingStrategy",
    "SVGTranslationExtractor",
]
