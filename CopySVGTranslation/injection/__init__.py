"""Injection phase helpers for CopySVGTranslation."""

from .exceptions import SvgNestedTspanExceptionError, SvgStructureExceptionError
from .preparation import SvgTranslationPreparer, make_translation_ready
from .svg_injector import InjectorData, SVGTranslationInjector
from .worker import inject, perform_svg_injection

__all__ = [
    "InjectorData",
    "perform_svg_injection",
    "inject",
    "SVGTranslationInjector",
    "SvgTranslationPreparer",
    "make_translation_ready",
    "SvgStructureExceptionError",
    "SvgNestedTspanExceptionError",
]
