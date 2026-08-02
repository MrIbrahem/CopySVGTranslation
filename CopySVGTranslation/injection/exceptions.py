"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class SvgStructureExceptionError(Exception):
    """Raised when SVG structure is unsuitable for translation."""

    def __init__(self, code: str, element=None, extra=None):
        """Store structured error details for later reporting.

        Parameters:
            code (str): Machine-readable error code describing the structural
                issue encountered.
            element: Optional XML element related to the error (for diagnostics).
            extra: Optional supplemental data used to enrich the exception
                message.
        """
        self.code = code
        self.element = element
        self.extra = extra
        msg = code
        if extra:
            msg += ": " + str(extra)
        super().__init__(msg)


class SvgNestedTspanExceptionError(SvgStructureExceptionError):
    """Raised when encountering nested ``<tspan>`` elements."""

    def __init__(self, element=None, extra=None, node_text=None):
        self.node_text = node_text
        super().__init__("structure-error-nested-tspans-not-supported", element, extra)

    def node(self):
        return " ".join(str(self.node_text).strip().split())


__all__ = [
    "SvgStructureExceptionError",
    "SvgNestedTspanExceptionError",
]
