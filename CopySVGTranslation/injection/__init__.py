"""Injection phase helpers for CopySVGTranslation."""

from .exceptions import SvgNestedTspanExceptionError, SvgStructureExceptionError
from .preparation import make_translation_ready
from .svg_injector import inject

__all__ = [
    "inject",
    "make_translation_ready",
    "SvgStructureExceptionError",
    "SvgNestedTspanExceptionError",
]
