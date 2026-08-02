"""Public API for the CopySVGTranslation package."""

from .extraction import SVGTranslationExtractor, extract
from .injection import InjectorData, SVGTranslationInjector, inject, perform_svg_injection
from .nested_analyze import fix_nested_file, match_nested_tags

__all__ = [
    "SVGTranslationInjector",
    "SVGTranslationExtractor",
    "match_nested_tags",
    "fix_nested_file",
    "InjectorData",
    # new API returns dataclass
    "perform_svg_injection",
    "inject",  # to be deprecated
    "extract",  # to be deprecated
]
