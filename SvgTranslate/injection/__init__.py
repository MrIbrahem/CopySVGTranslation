"""Injection phase helpers for SvgTranslate."""

from .batch import start_injects
from .injector import (
    generate_unique_id,
    inject,
    load_all_mappings,
    work_on_switches,
)
from .preparation import make_translation_ready, SvgStructureException

__all__ = [
    "generate_unique_id",
    "inject",
    "load_all_mappings",
    "make_translation_ready",
    "start_injects",
    "SvgStructureException",
    "work_on_switches",
]
