**Extraction Package Design**

```
extraction/
├── __init__.py
├── extractor.py           # SVGTranslationExtractor
└── strategies.py          # Matching strategies (how default text links to translations)
```

Extraction is the counterpart of injection: it reads a translation-ready (or real-world) SVG and builds a `TranslationMapping`.

---

### Responsibilities

1. Parse the SVG and find every `<switch>`.
2. Identify the **default / fallback** `<text>` (no `systemLanguage`).
3. Collect its text segments (from `<tspan>`s or the node itself).
4. Match translated `<text>` nodes (with `systemLanguage`) back to those defaults.
5. Build a `TranslationMapping` (`new`, optional `title_new`, diagnostics).
6. Optionally run `YearTitleHandler.build_templates()`.

The hard part is **step 4** — matching — which is why it is isolated behind strategies.

---

### Matching problem

Inside one `<switch>` you typically have:

```xml
<switch>
  <!-- fallback -->
  <text id="t1">
    <tspan id="trsvg1">Hello</tspan>
    <tspan id="trsvg2">World</tspan>
  </text>
  <!-- Arabic -->
  <text systemLanguage="ar" id="t1-ar">
    <tspan id="trsvg1-ar">مرحبا</tspan>
    <tspan id="trsvg2-ar">بالعالم</tspan>
  </text>
</switch>
```

We need a reliable way to know that `trsvg1-ar` corresponds to `trsvg1` (“Hello”).  
Different SVGs use different conventions, so matching is pluggable.

---

### 1. `strategies.py`

```python
# extraction/strategies.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from lxml import etree

from ..core.text_node import TextNode
from ..utils.text import normalize_text

SVG_NS = "http://www.w3.org/2000/svg"


@dataclass(slots=True)
class SegmentMatch:
    """One matched pair: default segment ↔ translated segment."""
    default_text: str
    translated_text: str
    default_id: str | None = None
    translated_id: str | None = None


class MatchingStrategy(ABC):
    """
    How to associate translated <text>/<tspan> content
    with the default (fallback) content inside the same <switch>.
    """

    @abstractmethod
    def match(
        self,
        default_node: TextNode,
        translated_node: TextNode,
        *,
        case_insensitive: bool = True,
    ) -> list[SegmentMatch]:
        """
        Return matched segments for one language node.
        The list length should normally equal the number of default segments.
        """
        ...


class ByTspanIdStrategy(MatchingStrategy):
    """
    Preferred strategy.

    Assumes translated tspan ids are derived from the default ids:
      trsvg12  →  trsvg12-ar  or  trsvg12_ar  or  ar-trsvg12  etc.

    Algorithm
    ---------
    1. Build map: base_id → default text  (base_id = id split on '-' / '_' [0])
    2. For each translated tspan, recover base_id and look up default text.
    """

    def match(
        self,
        default_node: TextNode,
        translated_node: TextNode,
        *,
        case_insensitive: bool = True,
    ) -> list[SegmentMatch]:
        # default id → text
        default_by_id: dict[str, str] = {}
        for tspan in default_node.tspans():
            tid = tspan.get("id")
            if not tid or not (tspan.text and tspan.text.strip()):
                continue
            base = tid.split("-")[0].split("_")[0].strip()
            text = normalize_text(tspan.text, case_insensitive)
            default_by_id[base] = text
            default_by_id[base.lower()] = text

        matches: list[SegmentMatch] = []
        for tspan in translated_node.tspans():
            tid = tspan.get("id")
            raw = (tspan.text or "").strip()
            if not tid or not raw:
                continue
            base = tid.split("-")[0].split("_")[0].strip()
            default_text = default_by_id.get(base) or default_by_id.get(base.lower())
            if default_text is None:
                continue
            matches.append(
                SegmentMatch(
                    default_text=default_text,
                    translated_text=normalize_text(raw),
                    default_id=base,
                    translated_id=tid,
                )
            )
        return matches


class ByPositionStrategy(MatchingStrategy):
    """
    Fallback strategy when ids are missing or unreliable.

    Matches segments by index order:
      default tspans[i] ↔ translated tspans[i]
    """

    def match(
        self,
        default_node: TextNode,
        translated_node: TextNode,
        *,
        case_insensitive: bool = True,
    ) -> list[SegmentMatch]:
        default_texts = default_node.texts(
            normalize=True, case_insensitive=case_insensitive
        )
        translated_texts = translated_node.texts(normalize=True, case_insensitive=False)

        matches: list[SegmentMatch] = []
        for i, def_text in enumerate(default_texts):
            if i >= len(translated_texts):
                break
            matches.append(
                SegmentMatch(
                    default_text=def_text,
                    translated_text=translated_texts[i],
                )
            )
        return matches


class CompositeMatchingStrategy(MatchingStrategy):
    """
    Try strategies in order; use the first one that returns any matches.
    Default pipeline: ByTspanId → ByPosition.
    """

    def __init__(self, strategies: list[MatchingStrategy] | None = None) -> None:
        self.strategies = strategies or [
            ByTspanIdStrategy(),
            ByPositionStrategy(),
        ]

    def match(
        self,
        default_node: TextNode,
        translated_node: TextNode,
        *,
        case_insensitive: bool = True,
    ) -> list[SegmentMatch]:
        for strategy in self.strategies:
            result = strategy.match(
                default_node,
                translated_node,
                case_insensitive=case_insensitive,
            )
            if result:
                return result
        return []
```

---

### 2. `extractor.py`

```python
# extraction/extractor.py
from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

from ..config import TranslationConfig
from ..core.mapping import TranslationMapping
from ..core.switch_node import SwitchNode
from ..core.text_node import TextNode
from ..io.svg_document import SvgDocument
from ..titles.year_handler import YearTitleHandler
from ..utils.text import normalize_text
from .strategies import CompositeMatchingStrategy, MatchingStrategy

logger = logging.getLogger(__name__)
SVG_NS = {"svg": "http://www.w3.org/2000/svg"}


class SVGTranslationExtractor:
    """
    Extract translations from an SVG into a TranslationMapping.
    """

    def __init__(
        self,
        config: TranslationConfig | None = None,
        matching_strategy: MatchingStrategy | None = None,
    ) -> None:
        self.config = config or TranslationConfig()
        self.strategy = matching_strategy or CompositeMatchingStrategy()
        self.year_handler = YearTitleHandler(self.config)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def extract(self, path: Path | str) -> TranslationMapping:
        """
        Load the SVG and return a TranslationMapping.
        Raises on fatal I/O or parse errors; returns an empty mapping
        when no switches/translations are found.
        """
        doc = SvgDocument.load(path, config=self.config)
        return self.extract_from_root(doc.root)

    def extract_from_root(self, root: etree._Element) -> TranslationMapping:
        mapping = TranslationMapping()
        switches = root.xpath("//svg:switch", namespaces=SVG_NS)
        logger.debug("Found %d switch elements", len(switches))

        for switch_el in switches:
            self._process_switch(SwitchNode(switch_el), mapping)

        if self.config.enable_year_titles and mapping.new:
            self.year_handler.build_templates(mapping)

        return mapping

    # ------------------------------------------------------------------
    # Per-switch logic
    # ------------------------------------------------------------------
    def _process_switch(
        self,
        switch: SwitchNode,
        mapping: TranslationMapping,
    ) -> None:
        default = switch.fallback()
        if default is None:
            return

        default_texts = default.texts(
            normalize=True,
            case_insensitive=self.config.case_insensitive,
        )
        if not any(default_texts):
            return

        # Record diagnostic id → text (optional)
        for tspan in default.tspans():
            tid = tspan.get("id")
            if tid and tspan.text and tspan.text.strip():
                mapping.tspans_by_id[tid] = tspan.text.strip()

        # Ensure keys exist in mapping.new
        for text in default_texts:
            key = normalize_text(text, self.config.case_insensitive)
            mapping.new.setdefault(key, {})

        # Match every language node
        for node in switch.text_nodes():
            if node.is_fallback:
                continue
            lang = node.language
            if not lang:
                continue

            matches = self.strategy.match(
                default,
                node,
                case_insensitive=self.config.case_insensitive,
            )
            for m in matches:
                key = normalize_text(m.default_text, self.config.case_insensitive)
                mapping.add(
                    key,
                    lang,
                    m.translated_text,
                    case_insensitive=False,  # key already normalized
                )
```

---

### 3. `extraction/__init__.py`

```python
from .extractor import SVGTranslationExtractor
from .strategies import (
    MatchingStrategy,
    ByTspanIdStrategy,
    ByPositionStrategy,
    CompositeMatchingStrategy,
)

__all__ = [
    "SVGTranslationExtractor",
    "MatchingStrategy",
    "ByTspanIdStrategy",
    "ByPositionStrategy",
    "CompositeMatchingStrategy",
]
```

---

### Flow

```
SVG file
  │
  ▼
SvgDocument.load()
  │
  ▼
For each <switch>:
  │
  ├─ find fallback TextNode
  ├─ collect default texts + ids
  │
  └─ for each language TextNode:
          MatchingStrategy.match(default, translated)
                │
                ├─ ByTspanIdStrategy   (preferred)
                └─ ByPositionStrategy  (fallback)
          │
          ▼
        mapping.add(source, lang, translated_text)
  │
  ▼
YearTitleHandler.build_templates(mapping)   # optional
  │
  ▼
TranslationMapping
```

---

### Design notes

| Decision | Rationale |
|----------|-----------|
| Strategy pattern for matching | Real SVGs differ (some have good ids, some don’t) |
| `ByTspanId` first, then `ByPosition` | Best accuracy when ids exist; still works when they don’t |
| Returns `TranslationMapping` directly | No more ad-hoc dicts / `ExtractorData` error strings |
| Uses `TextNode` / `SwitchNode` | Same domain language as injection |
| Year templates built at the end | Keeps extractor focused; title logic stays in `titles/` |
| Config-driven | `case_insensitive`, `enable_year_titles`, etc. |

---

### Extension points

- Add `ByExactTextOrderStrategy` or fuzzy matching later without touching the extractor.
- Inject a custom `MatchingStrategy` in tests or for a specific corpus.
- Expose strategy choice on `TranslationConfig` later if needed (`matching_strategy: str = "composite"`).

This completes the extraction side in a way that mirrors the clean injection design.
