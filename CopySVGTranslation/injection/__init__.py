"""Injection phase helpers for CopySVGTranslation."""

from .batch import start_injects
from .preparation import make_translation_ready
from .svg_injector import (
    generate_unique_id,
    inject,
    load_all_mappings,
    work_on_switches,
)
from .utils import SvgNestedTspanExceptionError, SvgStructureExceptionError

__all__ = [
    "generate_unique_id",
    "inject",
    "load_all_mappings",
    "make_translation_ready",
    "start_injects",
    "SvgStructureExceptionError",
    "SvgNestedTspanExceptionError",
    "work_on_switches",
]
