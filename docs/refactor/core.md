**Core Package Design**

```
core/
├── __init__.py
├── models.py          # Shared small types / enums if needed
├── text_node.py       # TextNode
├── switch_node.py     # SwitchNode
└── mapping.py         # TranslationEntry + TranslationMapping
```

This layer holds the **domain concepts** only. No file I/O, no lxml parsing details beyond what is necessary, and no knowledge of preparation or injection pipelines.

---

### 1. `mapping.py` — Translation data

```python
# core/mapping.py
from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class TranslationEntry:
    """One source string and its per-language translations."""

    source: str
    translations: Mapping[str, str] = field(default_factory=dict)

    def get(self, lang: str, default: str | None = None) -> str | None:
        return self.translations.get(lang, default)

    def languages(self) -> set[str]:
        return set(self.translations.keys())


@dataclass(slots=True)
class TranslationMapping:
    """
    Full mapping produced by extraction and consumed by injection.

    Attributes
    ----------
    new:
        Main map: normalized source text → {lang: translated text}
    title / title_new:
        Optional year-title variants (kept for compatibility / advanced use)
    tspans_by_id:
        Optional diagnostic map from extraction (id → default text)
    """
    new: dict[str, dict[str, str]] = field(default_factory=dict)
    title: dict[str, dict[str, str]] = field(default_factory=dict)
    title_new: dict[str, dict[str, str]] = field(default_factory=dict)
    tspans_by_id: dict[str, str] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_any(cls, data: Mapping[str, Any] | TranslationMapping) -> TranslationMapping:
        if isinstance(data, TranslationMapping):
            return data
        return cls(
            new=dict(data.get("new", {})),
            title_new=dict(data.get("title_new", {})),
            tspans_by_id=dict(data.get("tspans_by_id", {})),
            meta=dict(data.get("meta", {})),
        )

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def is_empty(self) -> bool:
        return not self.new and not self.title and not self.title_new

    def all_languages(self) -> set[str]:
        langs: set[str] = set()
        for section in (self.new, self.title, self.title_new):
            for trans in section.values():
                langs.update(trans.keys())
        return langs

    def lookup(self, source: str, *, case_insensitive: bool = True) -> dict[str, str]:
        """Return {lang: text} for a source string, or empty dict."""
        key = source.lower() if case_insensitive else source
        if case_insensitive:
            for k, v in self.new.items():
                if k.lower() == key:
                    return dict(v)
            return {}
        return dict(self.new.get(key, {}))

    def entries(self) -> Iterator[TranslationEntry]:
        for source, trans in self.new.items():
            yield TranslationEntry(source=source, translations=trans)

    # ------------------------------------------------------------------
    # Mutation helpers (used while building the mapping)
    # ------------------------------------------------------------------
    def add(self, source: str, lang: str, text: str, *, case_insensitive: bool = True) -> None:
        key = source.lower() if case_insensitive else source
        self.new.setdefault(key, {})[lang] = text

    def merge(self, other: TranslationMapping | Mapping[str, Any]) -> None:
        other = self.from_any(other)
        for source, trans in other.new.items():
            self.new.setdefault(source, {}).update(trans)
        for source, trans in other.title.items():
            self.title.setdefault(source, {}).update(trans)
        for source, trans in other.title_new.items():
            self.title_new.setdefault(source, {}).update(trans)
        self.tspans_by_id.update(other.tspans_by_id)

    def to_json(self) -> dict[str, Any]:
        return {
            "new": self.new,
            "title_new": self.title_new,
            "tspans_by_id": self.tspans_by_id,
            "meta": self.meta,
        }
```

---

### 2. `text_node.py` — Wrapper around `<text>` / `<tspan>`

```python
# core/text_node.py
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from lxml import etree

from ..utils.text import normalize_text

SVG_NS = "http://www.w3.org/2000/svg"


@dataclass(slots=True)
class TextNode:
    """
    Thin domain wrapper over an SVG <text> or <tspan> element.
    Does not own the element - it only provides a convenient API.
    """

    element: etree._Element

    # ------------------------------------------------------------------
    # Identity & language
    # ------------------------------------------------------------------
    @property
    def id(self) -> str | None:
        return self.element.get("id")

    @id.setter
    def id(self, value: str) -> None:
        self.element.set("id", value)

    @property
    def language(self) -> str | None:
        """systemLanguage or None for the fallback/default node."""
        return self.element.get("systemLanguage")

    @language.setter
    def language(self, value: str | None) -> None:
        if value is None:
            self.element.attrib.pop("systemLanguage", None)
        else:
            self.element.set("systemLanguage", value)

    @property
    def is_fallback(self) -> bool:
        return self.language is None

    # ------------------------------------------------------------------
    # Text content
    # ------------------------------------------------------------------
    def texts(self, *, normalize: bool = True, case_insensitive: bool = False) -> list[str]:
        """
        Return the list of text segments.
        Prefer direct child <tspan>s; fall back to the element's own text.
        """
        tspans = self.tspans()
        if tspans:
            raw = [t.text or "" for t in tspans]
        else:
            raw = [self.element.text or ""]

        if not normalize:
            return raw
        return [normalize_text(t, case_insensitive) for t in raw]

    def set_texts(self, texts: list[str]) -> None:
        """Write texts back into child tspans (or the element itself)."""
        tspans = list(self.tspans())
        if tspans:
            for i, tspan in enumerate(tspans):
                tspan.text = texts[i] if i < len(texts) else ""
        else:
            self.element.text = texts[0] if texts else ""

    def tspans(self) -> list[etree._Element]:
        return self.element.xpath("./svg:tspan", namespaces={"svg": SVG_NS})

    def iter_tspan_nodes(self) -> Iterator[TextNode]:
        for tspan in self.tspans():
            yield TextNode(tspan)

    # ------------------------------------------------------------------
    # Cloning
    # ------------------------------------------------------------------
    def clone(self) -> TextNode:
        """Deep clone the underlying element and wrap it."""
        import copy

        return TextNode(copy.deepcopy(self.element))
```

---

### 3. `switch_node.py` — Wrapper around `<switch>`

```python
# core/switch_node.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from lxml import etree

from .text_node import TextNode

SVG_NS = "http://www.w3.org/2000/svg"


@dataclass(slots=True)
class SwitchNode:
    """Domain wrapper over an SVG <switch> element."""

    element: etree._Element

    def text_nodes(self) -> list[TextNode]:
        texts = self.element.xpath("./svg:text", namespaces={"svg": SVG_NS})
        return [TextNode(t) for t in texts]

    def iter_text_nodes(self) -> Iterator[TextNode]:
        yield from self.text_nodes()

    def fallback(self) -> TextNode | None:
        """Return the default (no systemLanguage) text node, if any."""
        for node in self.text_nodes():
            if node.is_fallback:
                return node
        return None

    def default_text_node(self) -> TextNode | None:
        """Return the default (no systemLanguage) text node, if any."""
        return self.fallback()

    def existing_languages(self) -> set[str]:
        return {n.language for n in self.text_nodes() if n.language}

    def find_by_language(self, lang: str) -> TextNode | None:
        for node in self.text_nodes():
            if node.language == lang:
                return node
        return None

    def append(self, node: TextNode) -> None:
        self.element.append(node.element)

    def remove(self, node: TextNode) -> None:
        self.element.remove(node.element)

    def reorder(self, put_fallback_last: bool = True) -> None:
        """Deterministic ordering of child <text> elements."""
        nodes = self.text_nodes()

        def sort_key(n: TextNode):
            lang = n.language or "fallback"
            # Prefer numeric part of trsvg IDs when present
            import re

            m = re.search(r"trsvg(\d+)", n.id or "")
            num = int(m.group(1)) if m else 10**9
            is_fallback = 0 if n.is_fallback else 1
            return (is_fallback if put_fallback_last else 0, num, lang)

        ordered = sorted(nodes, key=sort_key)
        for n in ordered:
            self.element.remove(n.element)
        for n in ordered:
            self.element.append(n.element)
```

---

### 4. `models.py` — Small shared types (optional)

```python
# core/models.py
from __future__ import annotations

from enum import Enum
from typing import TypeAlias

# Re-export the main domain objects for convenience
from .mapping import TranslationEntry, TranslationMapping
from .text_node import TextNode
from .switch_node import SwitchNode


class NestedStrategy(str, Enum):
    PRESERVE_STYLE = "preserve_style"
    SPLIT_NESTED_TSPANS = "split_nested_tspans" # alias PRESERVE_STYLE
    FLATTEN = "flatten"
    RAISE = "raise"


# Common type aliases
LangCode: TypeAlias = str
SourceText: TypeAlias = str
```

---

### 5. `core/__init__.py`

```python
from .mapping import TranslationEntry, TranslationMapping
from .text_node import TextNode
from .switch_node import SwitchNode
from .models import NestedStrategy

__all__ = [
    "TranslationEntry",
    "TranslationMapping",
    "TextNode",
    "SwitchNode",
    "NestedStrategy",
]
```

---

### How the rest of the system uses Core

| Component              | Uses                                                                     |
| ---------------------- | ------------------------------------------------------------------------ |
| **Extractor**          | Builds a `TranslationMapping`                                            |
| **SwitchProcessor**    | Receives a `SwitchNode`, gets `fallback()`, reads `existing_languages()` |
| **TranslationApplier** | Works with `TextNode` (clone, set_texts, language, id)                   |
| **YearTitleHandler**   | Reads/writes `TranslationMapping.title` / `title_new`                    |
| **Service**            | Returns `TranslationMapping` inside `OperationResult`                    |
| **MappingStore**       | Serializes `TranslationMapping.to_json()` to JSON                        |

---

### Design principles for Core

1. **Thin wrappers** — `TextNode` and `SwitchNode` do not copy the XML tree; they only provide a safe, intention-revealing API.
2. **Immutable-friendly mapping** — `TranslationEntry` is frozen; `TranslationMapping` is mutable only while being built.
3. **No I/O** — Core never opens files or writes disk.
4. **No pipeline knowledge** — Core does not know about preparation steps or injection stats.
5. **Easy to test** — You can construct a `TranslationMapping` by hand and pass it to the injector without any SVG.

This gives the rest of the redesign a clear, stable domain language to work with.
