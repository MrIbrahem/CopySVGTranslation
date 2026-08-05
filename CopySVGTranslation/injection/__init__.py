"""Injection phase helpers for CopySVGTranslation."""

from .id_manager import IdManager
from .injector import InjectorData, SVGTranslationInjector
from .switch_processor import SwitchProcessor
from .translation_applier import ApplyResult, TranslationApplier

__all__ = [
    "IdManager",
    "InjectorData",
    "SVGTranslationInjector",
    "SwitchProcessor",
    "ApplyResult",
    "TranslationApplier",
]
