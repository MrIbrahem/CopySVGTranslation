"""Public API for the CopySVGTranslation package."""

__version__ = "2.0.1"

from .config import TranslationConfig
from .core.mapping import TranslationEntry, TranslationMapping
from .extraction import SVGTranslationExtractor
from .extraction.worker import extract
from .injection import InjectorData, SVGTranslationInjector
from .io.mapping_store import MappingStore
from .legacy import inject_file_tree
from .nested_analyze import NestedTspanDetector, fix_nested_file, match_nested_tags
from .result import InjectorStats, InjectResult, OperationResult
from .service import SVGTranslationService

__all__ = [
    # main API
    "TranslationConfig",
    "SVGTranslationInjector",
    "SVGTranslationExtractor",
    "SVGTranslationService",
    "MappingStore",
    "inject_file_tree",  # to be deprecated
    "extract",  # to be deprecated
    "NestedTspanDetector",
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
    "__version__",
]
