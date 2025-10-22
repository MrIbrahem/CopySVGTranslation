"""Shared text-handling helpers used by both extraction and injection."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def normalize_text(text: str | None, case_insensitive: bool = False) -> str:
    """Normalize text by trimming whitespace and optionally lowering the case."""
    if not text:
        return ""

    normalized = " ".join(text.strip().split())
    if case_insensitive:
        normalized = normalized.lower()

    return normalized


def extract_text_from_node(node) -> list[str]:
    """Extract text content from an SVG ``<text>`` element, honouring ``<tspan>``."""
    tspans = node.xpath('./svg:tspan', namespaces={'svg': 'http://www.w3.org/2000/svg'})
    if tspans:
        return [tspan.text.strip() if tspan.text else "" for tspan in tspans]

    return [node.text.strip()] if node.text else [""]
