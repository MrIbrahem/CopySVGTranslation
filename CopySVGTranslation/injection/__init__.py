"""Injection phase helpers for CopySVGTranslation."""

from .exceptions import SvgNestedTspanExceptionError, SvgStructureExceptionError
from .preparation import SvgTranslationPreparer, make_translation_ready
from .svg_injector import InjectorData, SVGTranslationInjector
from .worker import inject_file_and_save, inject_file_tree

__all__ = [
    "InjectorData",
    "inject_file_tree",
    "inject_file_and_save",
    "SVGTranslationInjector",
    "SvgTranslationPreparer",
    "make_translation_ready",
    "SvgStructureExceptionError",
    "SvgNestedTspanExceptionError",
]
