"""Injection phase helpers for CopySVGTranslation."""

from .id_manager import IdManager
from .injector import InjectorData, SVGTranslationInjector
from .switch_processor import SwitchProcessor
from .translation_applier import ApplyResult, TranslationApplier
from ..legacy.worker import inject_file_and_save, inject_file_tree

__all__ = [
    "IdManager",
    "InjectorData",
    "SVGTranslationInjector",
    "SwitchProcessor",
    "ApplyResult",
    "TranslationApplier",
    "inject_file_tree",
    "inject_file_and_save",
]
