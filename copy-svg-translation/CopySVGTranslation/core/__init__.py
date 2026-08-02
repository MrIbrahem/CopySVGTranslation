# core/__init__.py
from .mapping import TranslationEntry, TranslationMapping
from .models import NestedStrategy
from .switch_node import SwitchNode
from .text_node import TextNode

__all__ = [
    "TranslationEntry",
    "TranslationMapping",
    "TextNode",
    "SwitchNode",
    "NestedStrategy",
]
