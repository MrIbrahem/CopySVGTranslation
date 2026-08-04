"""Public API for the CopySVGTranslation package."""

from .config import TranslationConfig
from .core.mapping import TranslationMapping, TranslationEntry
from .extraction import SVGTranslationExtractor, extract
from .injection import InjectorData, SVGTranslationInjector, inject_file_tree
from .nested_analyze import fix_nested_file, match_nested_tags
from .service import SVGTranslationService
from .io.mapping_store import MappingStore
from .result import OperationResult, InjectorStats, InjectResult

__all__ = [
    # main API
    "TranslationConfig",
    "SVGTranslationInjector",
    "SVGTranslationExtractor",
    "SVGTranslationService",
    "MappingStore",
    "inject_file_tree",  # to be deprecated
    "extract",  # to be deprecated
    # dataclasses
    "TranslationMapping",
    "TranslationEntry",
    "InjectorData",
    "InjectorStats",
    "OperationResult",
    "InjectResult",
    # others
    "match_nested_tags",
    "fix_nested_file",
]
