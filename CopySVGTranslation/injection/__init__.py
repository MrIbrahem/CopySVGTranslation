"""Injection phase helpers for CopySVGTranslation."""

from .batch import start_injects
from .exceptions import SvgNestedTspanExceptionError, SvgStructureExceptionError
from .preparation import make_translation_ready
from .svg_injector import inject
from .utils import (
    generate_unique_id,
    load_all_mappings,
)

__all__ = [
    "generate_unique_id",
    "inject",
    "load_all_mappings",
    "make_translation_ready",
    "start_injects",
    "SvgStructureExceptionError",
    "SvgNestedTspanExceptionError",
]
