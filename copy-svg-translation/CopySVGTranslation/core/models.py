# core/models.py
from __future__ import annotations

from enum import Enum
from typing import TypeAlias

from .mapping import TranslationEntry, TranslationMapping
from .text_node import TextNode
from .switch_node import SwitchNode


class NestedStrategy(str, Enum):
    PRESERVE_STYLE = "preserve_style"
    FLATTEN = "flatten"
    RAISE = "raise"


LangCode: TypeAlias = str
SourceText: TypeAlias = str
