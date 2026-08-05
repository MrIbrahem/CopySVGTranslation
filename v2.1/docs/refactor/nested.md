**Nested Package Design**

```
nested/
├── __init__.py
├── detector.py          # NestedTspanDetector
└── flattener.py         # NestedTspanFlattener
```

This package is responsible for **detecting and fixing nested `<tspan>` (and `<a>`) elements**, which the rest of the system does not support directly.

It replaces both:

-   `nested/find_nested.py` (simple flatten)
-   `nested/find_nested_new.py` (style-preserving attempt)

---

### Responsibility

SVG files often contain structures like:

```xml
<text>
  <tspan>
    <tspan style="font-weight:700">Data source:</tspan>
    United Nations ...
  </tspan>
</text>
```

The translation pipeline requires **flat** tspans (no element children).
This package offers three strategies (controlled by `TranslationConfig.nested_strategy`):

| Strategy              | Behaviour                                                                  |
| --------------------- | -------------------------------------------------------------------------- |
| `preserve_style`      | Turn nested styled tspans into **sibling** tspans (keeps bold/italic etc.) |
| `split_nested_tspans` | Turn nested styled tspans into **sibling** tspans (keeps bold/italic etc.) |
| `flatten`             | Concatenate all text into a single tspan (loses inner styling)             |
| `raise`               | Raise `SvgNestedTspanError`                                                |

---

### 1. `detector.py`

```python
# nested/detector.py
from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

logger = logging.getLogger(__name__)
SVG_NS = "http://www.w3.org/2000/svg"


class NestedTspanDetector:
    """
    Find <tspan> elements that contain nested element children.
    Useful for diagnostics and pre-flight checks.
    """

    def __init__(self, tags: tuple[str, ...] = ("tspan", "a")) -> None:
        self.tags = tags

    def find_in_tree(self, root: etree._Element) -> list[etree._Element]:
        """Return all tspan elements that have element children."""
        result: list[etree._Element] = []
        for tspan in root.findall(f".//{{{SVG_NS}}}tspan"):
            element_children = [c for c in tspan if isinstance(c.tag, str)]
            if element_children:
                result.append(tspan)
        return result

    def find_in_file(self, path: Path | str) -> list[str]:
        """
        Parse a file and return serialised representations of nested tspans.
        Returns an empty list on parse errors.
        """
        path = Path(path)
        if not path.exists():
            logger.error("File does not exist: %s", path)
            return []

        try:
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse(str(path), parser)
            root = tree.getroot()
            if root is None:
                return []
        except (etree.XMLSyntaxError, OSError) as exc:
            logger.error("Failed to parse %s: %s", path, exc)
            return []

        nested = self.find_in_tree(root)
        return [
            etree.tostring(t, pretty_print=False,).decode("utf-8")
            for t in nested
        ]

    def has_nested(self, root: etree._Element) -> bool:
        return bool(self.find_in_tree(root))
```

---

### 2. `flattener.py`

```python
# nested/flattener.py
from __future__ import annotations

import logging
from typing import Literal

from lxml import etree

from ..exceptions import SvgNestedTspanError

logger = logging.getLogger(__name__)
SVG_NS = "http://www.w3.org/2000/svg"

NestedStrategy = Literal["split_nested_tspans", "preserve_style", "flatten", "raise"]


def _flatten_text(elem: etree._Element) -> str:
    """Recursively collect text and tails preserving order."""
    parts: list[str] = []
    if elem.text:
        parts.append(elem.text)
    for child in elem:
        parts.append(_flatten_text(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


class NestedTspanFlattener:
    """
    Fix nested <tspan> / <a> elements according to the chosen strategy.
    """

    def __init__(
        self,
        strategy: NestedStrategy = "preserve_style",
        *,
        also_fix_a: bool = True,
    ) -> None:
        self.strategy = strategy
        self.also_fix_a = also_fix_a

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def process(self, root: etree._Element) -> etree._Element:
        """
        Process the tree in-place and return the root.
        """
        if self.strategy == "raise":
            self._raise_if_nested(root)
            return root

        if self.strategy == "flatten":
            self._flatten_all(root, tag="tspan")
            if self.also_fix_a:
                self._flatten_all(root, tag="a")
            return root

        # preserve_style / split_nested_tspans (default)
        self._preserve_style(root, tag="tspan")
        if self.also_fix_a:
            # <a> inside tspan is also invalid for many tools
            self._preserve_style(root, tag="a")
        return root

    # ------------------------------------------------------------------
    # Strategy: raise
    # ------------------------------------------------------------------
    def _raise_if_nested(self, root: etree._Element) -> None:
        for tspan in root.findall(f".//{{{SVG_NS}}}tspan"):
            element_children = [c for c in tspan if isinstance(c.tag, str)]
            if element_children:
                node_text = etree.tostring(tspan, pretty_print=True).decode("utf-8")
                raise SvgNestedTspanError(
                    element=tspan,
                    extra=[tspan.get("id", "")],
                    node_text=node_text,
                )

    # ------------------------------------------------------------------
    # Strategy: flatten
    # ------------------------------------------------------------------
    def _flatten_all(self, root: etree._Element, tag: str) -> None:
        for tspan in root.findall(f".//{{{SVG_NS}}}tspan"):
            nested = tspan.findall(f".//{{{SVG_NS}}}{tag}")
            if not nested:
                continue
            flattened = _flatten_text(tspan)
            for child in list(tspan):
                tspan.remove(child)
            tspan.text = flattened
            tspan.tail = None

    # ------------------------------------------------------------------
    # Strategy: preserve_style
    # ------------------------------------------------------------------
    def _preserve_style(self, root: etree._Element, tag: str) -> None:
        """
        Convert nested tspans into sibling tspans so styling is kept.

        Example
        -------
        Before:
            <tspan x="16" y="581">
                <tspan style="font-weight:700">Data source:</tspan>
                United Nations ...
            </tspan>

        After:
            <tspan style="font-weight:700">Data source:</tspan>
            <tspan>United Nations ...</tspan>
        """
        # Process per parent <text> so we can safely replace children
        for parent in root.findall(f".//{{{SVG_NS}}}text"):
            direct_tspans = [
                child for child in parent
                if child.tag == f"{{{SVG_NS}}}tspan"
            ]

            for tspan in direct_tspans:
                nested_children = [
                    child for child in tspan
                    if child.tag == f"{{{SVG_NS}}}{tag}"
                ]
                if not nested_children:
                    continue

                parent_list = list(parent)
                index = parent_list.index(tspan)
                new_siblings: list[etree._Element] = []

                # Text that belongs to the outer tspan (before any children)
                if tspan.text and tspan.text.strip():
                    outer = etree.Element(f"{{{SVG_NS}}}tspan")
                    outer.text = tspan.text
                    # optionally copy non-position attributes from outer tspan
                    new_siblings.append(outer)

                for nested in nested_children:
                    new_tspan = etree.Element(f"{{{SVG_NS}}}tspan")
                    for k, v in nested.attrib.items():
                        new_tspan.set(k, v)
                    new_tspan.text = nested.text
                    new_siblings.append(new_tspan)

                    # Tail after the nested element
                    if nested.tail and nested.tail.strip():
                        tail_tspan = etree.Element(f"{{{SVG_NS}}}tspan")
                        tail_tspan.text = nested.tail
                        new_siblings.append(tail_tspan)

                # Replace the original nested tspan with the new siblings
                parent.remove(tspan)
                for i, sibling in enumerate(new_siblings):
                    parent.insert(index + i, sibling)
```

---

### 3. `nested/__init__.py`

```python
from .detector import NestedTspanDetector
from .flattener import NestedTspanFlattener

__all__ = [
    "NestedTspanDetector",
    "NestedTspanFlattener",
]
```

---

### Integration points

| Caller                                   | How it uses nested/                                                    |
| ---------------------------------------- | ---------------------------------------------------------------------- |
| **NormalizeTspans** (preparation step)   | `NestedTspanFlattener(config.nested_strategy).process(root)`           |
| **ValidateStructure** (preparation step) | If strategy is `"raise"`, can call detector or let the flattener raise |
| **Service / CLI**                        | Optional pre-check: `NestedTspanDetector().find_in_file(path)`         |
| **Legacy `fix_nested_file`**             | Thin wrapper around `NestedTspanFlattener` + `SvgDocument.save`        |

---

### Flow inside Preparation

```
ValidateStructure
       │
       ▼
NormalizeTspans
       │
       ├─► NestedTspanFlattener(strategy).process(root)
       │         • preserve_style  (default)
       │         • flatten
       │         • raise
       │
       └─► wrap any remaining loose text into <tspan>
```

---

### Design notes

1. **Strategy pattern via config** — one place controls behaviour (`TranslationConfig.nested_strategy`).
2. **`preserve_style` is default** — keeps visual formatting whenever possible.
3. **Handles both `<tspan>` and `<a>`** — many real-world SVGs put links inside text.
4. **In-place processing** — works directly on the lxml tree already loaded by Preparation.
5. **Clear separation** — Detector is read-only / diagnostic; Flattener performs the mutation.
6. **Testable** — pure tree transforms; no filesystem dependency in the core logic.

This gives the redesign a robust, configurable solution for the nested-tspan problem that used to be split across two incomplete modules.
