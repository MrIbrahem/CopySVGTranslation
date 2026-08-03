"""Public API for the CopySVGTranslation package."""

from .extraction import ExtractorData, SVGTranslationExtractor, extract
from .injection import InjectorData, SVGTranslationInjector, inject_file_tree
from .nested_analyze import fix_nested_file, match_nested_tags
from .workflows import svg_translate_between_files, svg_inject_translations

__all__ = [
    # main API
    "SVGTranslationInjector",
    "SVGTranslationExtractor",
    "inject_file_tree",  # to be deprecated
    "extract",  # to be deprecated
    # dataclasses
    "ExtractorData",
    "InjectorData",
    # workflows
    "svg_translate_between_files",
    "svg_inject_translations",
    # others
    "match_nested_tags",
    "fix_nested_file",
]
