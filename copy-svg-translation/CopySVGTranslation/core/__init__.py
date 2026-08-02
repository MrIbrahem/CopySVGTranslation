# core/__init__.py
from .mapping import TranslationEntry, TranslationMapping
from .text_node import TextNode
from .switch_node import SwitchNode
from .models import NestedStrategy

__all__ = [
    "TranslationEntry",
    "TranslationMapping",
    "TextNode",
    "SwitchNode",
    "NestedStrategy",
]
