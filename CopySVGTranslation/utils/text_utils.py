"""Shared text-handling helpers used by both extraction and injection."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


def normalize_lang(lang: str) -> str:
    """
    Normalize a language tag to a simple IETF-like form.
    This is a lightweight normalizer not a full BCP47 parser.
    Examples:
      'en_us' -> 'en-US'
      'EN' -> 'en'
      'pt-br' -> 'pt-BR'
    """
    if not lang:
        return lang
    pieces = re.split(r"[_\-\s]+", lang.strip())
    primary = pieces[0].lower()
    if len(pieces) > 1:
        rest = "-".join(p.upper() if len(p) == 2 else p.title() for p in pieces[1:])
        return f"{primary}-{rest}"
    return primary


def normalize_text(text: str | None, case_insensitive: bool = False) -> str:
    """Normalize text by trimming whitespace and optionally lowering the case."""
    if not text:
        return ""

    normalized = " ".join(text.strip().split())
    if case_insensitive:
        normalized = normalized.lower()

    return normalized


__all__ = [
    "normalize_lang",
    "normalize_text",
]
