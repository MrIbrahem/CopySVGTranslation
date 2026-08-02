# utils/text.py
from __future__ import annotations

import re


def normalize_text(text: str | None, case_insensitive: bool = False) -> str:
    """
    Trim, collapse internal whitespace, optionally lowercase.

    Examples
    --------
    >>> normalize_text("  Hello   World  ")
    'Hello World'
    >>> normalize_text("  Hello   World  ", case_insensitive=True)
    'hello world'
    """
    if not text:
        return ""
    normalized = " ".join(text.strip().split())
    if case_insensitive:
        normalized = normalized.lower()
    return normalized


def normalize_lang(lang: str) -> str:
    """
    Lightweight language-tag normalizer (not a full BCP-47 parser).

    Examples
    --------
    >>> normalize_lang("en_us")
    'en-US'
    >>> normalize_lang("EN")
    'en'
    >>> normalize_lang("pt-br")
    'pt-BR'
    >>> normalize_lang("zh_hans")
    'zh-Hans'
    """
    if not lang:
        return lang
    pieces = re.split(r"[_\-\s]+", lang.strip())
    primary = pieces[0].lower()
    if len(pieces) == 1:
        return primary
    rest = "-".join(p.upper() if len(p) == 2 else p.title() for p in pieces[1:])
    return f"{primary}-{rest}"


def split_lang_list(value: str | None) -> list[str]:
    """
    Split a (possibly comma-separated) systemLanguage value
    and normalize each tag.

    >>> split_lang_list("ar, fr, pt-br")
    ['ar', 'fr', 'pt-BR']
    >>> split_lang_list(None)
    []
    """
    if not value or not value.strip():
        return []
    return [normalize_lang(part) for part in re.split(r"\s*,\s*", value.strip()) if part]
