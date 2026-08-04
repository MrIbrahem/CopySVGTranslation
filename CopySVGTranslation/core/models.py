# core/models.py
from __future__ import annotations

from enum import Enum
from typing import TypeAlias


class NestedStrategy(str, Enum):
    PRESERVE_STYLE = "preserve_style"
    FLATTEN = "flatten"
    RAISE = "raise"


# Common type aliases
LangCode: TypeAlias = str
SourceText: TypeAlias = str
