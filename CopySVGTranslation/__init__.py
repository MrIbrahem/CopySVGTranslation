"""
Public API for the CopySVGTranslation package.

Used in copy-svg-langs project:
from CopySVGTranslation import SVGTranslationExtractor, TranslationConfig
from CopySVGTranslation import SVGTranslationInjector
from CopySVGTranslation import NestedTspanDetector, NestedTspanFlattener

"""

__version__ = "2.0.1"

from .config import TranslationConfig
from .core.mapping import TranslationEntry, TranslationMapping
from .extraction import SVGTranslationExtractor
from .injection import InjectorData, SVGTranslationInjector
from .io import MappingStore, SvgDocument
from .legacy import extract, inject_file_tree
from .nested import NestedTspanDetector, NestedTspanFlattener
from .result import InjectorStats, InjectResult, OperationResult
from .service import SVGTranslationService

__all__ = [
    # main API
    "TranslationConfig",
    "SVGTranslationInjector",
    "SVGTranslationExtractor",
    "SVGTranslationService",
    "MappingStore",
    "SvgDocument",
    "inject_file_tree",  # to be deprecated
    "extract",  # to be deprecated
    "NestedTspanDetector",
    "NestedTspanFlattener",
    # dataclasses
    "TranslationMapping",
    "TranslationEntry",
    "InjectorData",
    "InjectorStats",
    "OperationResult",
    "InjectResult",
    "__version__",
]
