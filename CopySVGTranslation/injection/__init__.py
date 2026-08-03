"""Injection phase helpers for CopySVGTranslation."""

from ..exceptions import SvgNestedTspanError, SvgStructureError
from .injector import InjectorData, SVGTranslationInjector
from .worker import inject_file_and_save, inject_file_tree

__all__ = [
    "InjectorData",
    "inject_file_tree",
    "inject_file_and_save",
    "SVGTranslationInjector",
    "SvgStructureError",
    "SvgNestedTspanError",
]
