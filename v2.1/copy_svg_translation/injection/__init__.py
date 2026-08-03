# injection/__init__.py
from .id_manager import IdManager
from .injector import SVGTranslationInjector
from .switch_processor import SwitchProcessor
from .translation_applier import ApplyResult, TranslationApplier
__all__ = [
    "IdManager",
    "SVGTranslationInjector",
    "SwitchProcessor",
    "ApplyResult",
    "TranslationApplier",
]


