"""Injection phase helpers for CopySVGTranslation."""

from .exceptions import SvgNestedTspanExceptionError, SvgStructureExceptionError
from .preparation import make_translation_ready
from .svg_injector import SVGTranslationInjector
from .worker import inject

__all__ = [
    "inject",
    "SVGTranslationInjector",
    "make_translation_ready",
    "SvgStructureExceptionError",
    "SvgNestedTspanExceptionError",
]
