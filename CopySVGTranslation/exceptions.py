# exceptions.py
from __future__ import annotations

from typing import Any


class CopySVGTranslationError(Exception):
    """Base error for the whole package."""

    def __init__(
        self,
        message: str = "",
        # *,
        code: str | None = None,
        element: Any = None,
        extra: Any = None,
    ) -> None:
        self.code = code or self.default_code()
        self.element = element
        self.extra = extra

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
