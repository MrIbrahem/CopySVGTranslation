# core/models.py
from __future__ import annotations

from enum import Enum
from typing import TypeAlias


class NestedStrategy(str, Enum):
    PRESERVE_STYLE = "preserve_style"
    SPLIT_NESTED_TSPANS = "split_nested_tspans" # alias PRESERVE_STYLE
    FLATTEN = "flatten"
    RAISE = "raise"


# Common type aliases
LangCode: TypeAlias = str
SourceText: TypeAlias = str


__all__ = [
    "NestedStrategy",
]
