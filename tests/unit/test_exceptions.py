# ruff: noqa: F401
"""
Unit tests for CopySVGTranslation/CopySVGTranslation/exceptions.py module.

Classes to test: CopySVGTranslationError, SvgStructureError, SvgNestedTspanError, SvgInvalidIdError, SvgContainsTrefError, SvgCssTooComplexError, SvgCssHasIdsError, SvgTextContainsDollarError, SvgSwitchStructureError, SvgNoParentForTextError, SvgNonTspanInsideTextError, SvgParseError, SvgIOError, MappingError, ConfigurationError

TODO: write tests
"""


from CopySVGTranslation.exceptions import (
    ConfigurationError,
    CopySVGTranslationError,
    MappingError,
    SvgContainsTrefError,
    SvgCssHasIdsError,
    SvgCssTooComplexError,
    SvgInvalidIdError,
    SvgIOError,
    SvgNestedTspanError,
    SvgNonTspanInsideTextError,
    SvgNoParentForTextError,
    SvgParseError,
    SvgStructureError,
    SvgSwitchStructureError,
    SvgTextContainsDollarError,
)
