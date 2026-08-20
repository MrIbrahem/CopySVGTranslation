# exceptions.py
from __future__ import annotations

from typing import Any

i18n_data = {
    "invalid-format": "Only SVG files are supported.",
    "invalid-svg": "Error reading file.",
    "structure-error-no-doc-element": "No document element found.",
    "structure-error-nested-tspans-not-supported": "This file can not be translated because it contains nested tspan elements in $1.",
    "structure-error-multiple-text-same-lang": "Multiple text elements found with language code '$2' (in element with ID '$1').",
    "structure-error-contains-tref": "This file contains tref tags, which are not supported by this tool.",
    "structure-error-css-too-complex": "This file contains CSS that is too complicated to parse.",
    "structure-error-css-has-ids": "This file uses element IDs in the CSS, which may break when SVG Translate adds new IDs. It should use classes instead, if possible.",
    "structure-error-unexpected-node-in-text": "This file has unexpected content within a text element. Only tspan elements should be used within text.",
    "structure-error-invalid-node-id": "This file contains a text element ID ($1) that contains characters that are not permitted with SVG Translate.",
    "structure-error-text-contains-dollar": "This file contains unsupported text content in $1 ('$2'). SVG Translate is not able to work with the dollar-number syntax.",
    "structure-error-non-tspan-inside-text": "This file contains a text element with content that is not a tspan element.",
    "structure-error-switch-text-is-not-node": "This file has non-node content within a switch element.",
    "structure-error-switch-text-content-outside-text": "This file has text content inside a switch element but outside of a text tag, and SVG Translate can not handle this.",
    "structure-error-switch-child-not-text": "This file contains a switch element that contains an element that is not a text element.",
    "structure-error-multiple-lang-in-text": "This file contains a text elements that have a repeated language code '$2' in the systemLanguage attributes.",
    "structure-error-no-id": "[element ID could be determined]",
}


class CopySVGTranslationError(Exception):
    """Base error for the whole package."""

    def __init__(
        self,
        message: str = "",
        *,
        code: str | None = None,
        element: Any = None,
        extra: Any = None,
    ) -> None:
        self.code = code or self.default_code()
        self.element = element
        self.extra = extra
        self.label = i18n_data.get(self.code, "")

        parts = [self.code]
        if message:
            parts.append(message)
        if extra is not None:
            parts.append(str(extra))
        super().__init__(": ".join(parts))

    @classmethod
    def default_code(cls) -> str:
        return "error"


# ------------------------------------------------------------------
# Structure errors (preparation / validation)
# ------------------------------------------------------------------
class SvgStructureError(CopySVGTranslationError):
    """SVG structure is unsuitable for translation."""

    @classmethod
    def default_code(cls) -> str:
        return "structure-error"


class SvgNestedTspanError(SvgStructureError):
    """Nested <tspan> (or <a>) elements are not allowed under current strategy."""

    def __init__(
        self,
        message: str = "",
        *,
        element: Any = None,
        extra: Any = None,
        node_text: str | None = None,
    ) -> None:
        self.node_text = node_text
        super().__init__(
            message,
            code="structure-error-nested-tspans-not-supported",
            element=element,
            extra=extra,
        )

    def node_preview(self) -> str:
        if not self.node_text:
            return ""
        return " ".join(str(self.node_text).strip().split())


class SvgInvalidIdError(SvgStructureError):
    @classmethod
    def default_code(cls) -> str:
        return "structure-error-invalid-node-id"


class SvgContainsTrefError(SvgStructureError):
    @classmethod
    def default_code(cls) -> str:
        return "structure-error-contains-tref"


class SvgCssTooComplexError(SvgStructureError):
    @classmethod
    def default_code(cls) -> str:
        return "structure-error-css-too-complex"


class SvgCssHasIdsError(SvgStructureError):
    @classmethod
    def default_code(cls) -> str:
        return "structure-error-css-has-ids"


class SvgTextContainsDollarError(SvgStructureError):
    @classmethod
    def default_code(cls) -> str:
        return "structure-error-text-contains-dollar"


class SvgSwitchStructureError(SvgStructureError):
    """Invalid children or duplicate languages inside a <switch>."""

    @classmethod
    def default_code(cls) -> str:
        return "structure-error-switch"


class SvgNoParentForTextError(SvgStructureError):
    @classmethod
    def default_code(cls) -> str:
        return "structure-error-no-parent-for-text"


class SvgNonTspanInsideTextError(SvgStructureError):
    @classmethod
    def default_code(cls) -> str:
        return "structure-error-non-tspan-inside-text"


# ------------------------------------------------------------------
# Parse / I/O
# ------------------------------------------------------------------
class SvgParseError(CopySVGTranslationError):
    """XML parsing failed."""

    @classmethod
    def default_code(cls) -> str:
        return "parse-error"


class SvgIOError(CopySVGTranslationError):
    """Filesystem related failure (missing file, write error, …)."""

    @classmethod
    def default_code(cls) -> str:
        return "io-error"


# ------------------------------------------------------------------
# Mapping / config
# ------------------------------------------------------------------
class MappingError(CopySVGTranslationError):
    """Translation mapping is missing, empty, or invalid."""

    @classmethod
    def default_code(cls) -> str:
        return "mapping-error"


class ConfigurationError(CopySVGTranslationError):
    """Invalid or inconsistent TranslationConfig."""

    @classmethod
    def default_code(cls) -> str:
        return "config-error"


__all__ = [
    "CopySVGTranslationError",
    "SvgStructureError",
    "SvgNestedTspanError",
    "SvgInvalidIdError",
    "SvgContainsTrefError",
    "SvgCssTooComplexError",
    "SvgCssHasIdsError",
    "SvgTextContainsDollarError",
    "SvgSwitchStructureError",
    "SvgNoParentForTextError",
    "SvgNonTspanInsideTextError",
    "SvgParseError",
    "SvgIOError",
    "MappingError",
    "ConfigurationError",
]
