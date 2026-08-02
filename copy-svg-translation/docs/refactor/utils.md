**Utils Package Design**

```
utils/
├── __init__.py
├── text.py          # normalize_text, normalize_lang
└── xml.py           # thin lxml / SVG helpers
```

Shared, dependency-light helpers used by core, extraction, injection, and titles.
No business logic, no file I/O, no knowledge of mappings or pipelines.

---

### 1. `text.py`

```python
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
    rest = "-".join(
        p.upper() if len(p) == 2 else p.title()
        for p in pieces[1:]
    )
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
    return [
        normalize_lang(part)
        for part in re.split(r"\s*,\s*", value.strip())
        if part
    ]
```

---

### 2. `xml.py`

```python
# utils/xml.py
from __future__ import annotations

import re
from typing import Iterable

from lxml import etree

SVG_NS = "http://www.w3.org/2000/svg"
SVG_NSMAP = {"svg": SVG_NS}


def svg_tag(local: str) -> str:
    """Return a Clark-notation tag for the SVG namespace."""
    return f"{{{SVG_NS}}}{local}"


def local_name(element: etree._Element) -> str:
    """Return the local tag name without namespace."""
    tag = element.tag
    if isinstance(tag, str) and tag.startswith("{"):
        return tag.rsplit("}", 1)[-1]
    return str(tag)


def is_svg_element(element: etree._Element, name: str) -> bool:
    """Check whether element is an SVG element with the given local name."""
    return element.tag in (svg_tag(name), name)


def findall_svg(root: etree._Element, name: str) -> list[etree._Element]:
    """Find all descendant elements with the given SVG local name."""
    return root.findall(f".//{{{SVG_NS}}}{name}")


def xpath_svg(root: etree._Element, expression: str):
    """Run an XPath expression with the standard svg prefix bound."""
    return root.xpath(expression, namespaces=SVG_NSMAP)


def extract_text_segments(node: etree._Element) -> list[str]:
    """
    Extract text segments from a <text> (or similar) node.
    Prefers direct child <tspan>s; falls back to the node's own text.
    """
    tspans = node.xpath("./svg:tspan", namespaces=SVG_NSMAP)
    if tspans:
        return [t.text.strip() if t.text else "" for t in tspans]
    return [node.text.strip()] if node.text else [""]


def get_text_content(element: etree._Element) -> str:
    """Return concatenated text content (like DOM textContent)."""
    return "".join(element.itertext())


def collect_ids(root: etree._Element) -> set[str]:
    """Return the set of all id attribute values in the tree."""
    return {id_ for id_ in root.xpath("//@id") if id_}


def sort_switch_children(
    switch: etree._Element,
    *,
    put_fallback_last: bool = True,
) -> None:
    """
    Deterministically reorder <text> children of a <switch>.
    Fallback (no systemLanguage) goes last by default.
    """
    texts = [
        c for c in switch
        if isinstance(c.tag, str) and is_svg_element(c, "text")
    ]

    def sort_key(el: etree._Element):
        lang = el.get("systemLanguage") or "fallback"
        m = re.search(r"trsvg(\d+)", el.get("id") or "")
        num = int(m.group(1)) if m else 10**9
        is_fallback = 0 if el.get("systemLanguage") is None else 1
        primary = is_fallback if put_fallback_last else 0
        return (primary, num, lang)

    ordered = sorted(texts, key=sort_key)
    for t in ordered:
        switch.remove(t)
    for t in ordered:
        switch.append(t)


def tree_languages(tree: etree._ElementTree | None) -> set[str]:
    """Return the set of systemLanguage values present in the tree."""
    if tree is None:
        return set()
    root = tree.getroot()
    if root is None:
        return set()
    langs: set[str] = set()
    for text in findall_svg(root, "text"):
        lang = text.get("systemLanguage")
        if lang:
            langs.add(lang)
    return langs
```

---

### 3. `utils/__init__.py`

```python
from .text import normalize_text, normalize_lang, split_lang_list
from .xml import (
    SVG_NS,
    SVG_NSMAP,
    svg_tag,
    local_name,
    is_svg_element,
    findall_svg,
    xpath_svg,
    extract_text_segments,
    get_text_content,
    collect_ids,
    sort_switch_children,
    tree_languages,
)

__all__ = [
    # text
    "normalize_text",
    "normalize_lang",
    "split_lang_list",
    # xml
    "SVG_NS",
    "SVG_NSMAP",
    "svg_tag",
    "local_name",
    "is_svg_element",
    "findall_svg",
    "xpath_svg",
    "extract_text_segments",
    "get_text_content",
    "collect_ids",
    "sort_switch_children",
    "tree_languages",
]
```

---

### Who uses what

| Helper                                  | Typical users                                                     |
| --------------------------------------- | ----------------------------------------------------------------- |
| `normalize_text`                        | Extractor, Injector, TextNode, YearTitleHandler, MatchingStrategy |
| `normalize_lang` / `split_lang_list`    | Preparation (`SplitLanguages`), any language handling             |
| `extract_text_segments`                 | TextNode, legacy paths                                            |
| `get_text_content`                      | Validation steps                                                  |
| `collect_ids`                           | IdManager, AssignIds step                                         |
| `sort_switch_children`                  | ReorderTexts step, final housekeeping in injector                 |
| `tree_languages`                        | Injector stats (before/after)                                     |
| `findall_svg` / `xpath_svg` / `svg_tag` | Everywhere that touches the tree                                  |

---

### Design notes

1. **Two files only** — text concerns vs XML/SVG concerns.
2. **No config dependency** — pure functions; callers pass `case_insensitive` etc.
3. **No raising of domain exceptions** — utils stay low-level; higher layers decide policy.
4. **Replaces old scattered helpers** — `text_utils.py`, parts of `elements_utils.py`, and duplicated XPath/namespace constants.
5. **Easy to test** — pure functions, no filesystem, minimal lxml surface.

This finishes the shared foundation that core, extraction, injection, titles, and nested all rely on.

---

### Remaining after utils

| Part                                    | Status        |
| --------------------------------------- | ------------- |
| `legacy/` wrappers                      | Optional next |
| Package root `__init__.py` (public API) | Optional next |
| CLI                                     | Low priority  |

Everything required for the modern class-based core is now designed.
