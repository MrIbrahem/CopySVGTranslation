"""Public API for the CopySVGTranslation package."""

from .config import TranslationConfig
from .core.mapping import TranslationMapping
from .extraction import SVGTranslationExtractor, extract
from .injection import InjectorData, SVGTranslationInjector, inject_file_tree
from .nested_analyze import fix_nested_file, match_nested_tags

__all__ = [
    # main API
    "TranslationConfig",
    "SVGTranslationInjector",
    "SVGTranslationExtractor",
    "inject_file_tree",  # to be deprecated
    "extract",  # to be deprecated
    # dataclasses
    "TranslationMapping",
    "InjectorData",
    # others
    "match_nested_tags",
    "fix_nested_file",
]
