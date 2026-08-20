"""Internal extraction components for CopySVGTranslation."""

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
]
