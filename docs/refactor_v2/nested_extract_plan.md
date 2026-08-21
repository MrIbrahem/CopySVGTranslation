# Draft: `nested/` & `extraction/` Refactor

Scope: **nested** and **extraction** only (preparation/steps already covered).

---

## Part A — `nested/`

### Current state

| File | Role | Issues |
|------|------|--------|
| `detector.py` | Find nested `<tspan>` / `<a>` | Good, keep |
| `flattener.py` | Apply strategy (`raise` / `flatten` / `preserve_style`) | Good, keep |

### Target design

```text
nested/
  detector.py      # unchanged (minor cleanups OK)
  flattener.py     # unchanged (single source of truth for strategies)
  __init__.py      # export Detector + Flattener only
```

### Proposed changes

#### 1. `NestedTspanDetector` — small cleanups only

- Keep `find_in_tree`, `has_nested`, `find_in_tree_return_list`.
- Deprecate or narrow `find_in_file` (I/O belongs outside the library core).
- Optional: accept configurable tags via constructor (already present).

#### 2. `NestedTspanFlattener` — no structural change

- Remains the only place that mutates the tree according to `nested_strategy`.
- Used exclusively by `preparation.steps.NormalizeTspans`.

#### 3. `MatchFixNestedTags` (`fixer.py`) — remove or demote

**Option A (recommended):** Delete from public package API.

**Option B:** Move to legacy / thin CLI helper:

```text
legacy/fix_nested.py
  or
tools/fix_nested_svg.py
```

Draft of a thin replacement (if a file-based helper is still needed):

```python
# legacy/fix_nested.py  (optional, not part of core nested/)
from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

from ..nested.detector import NestedTspanDetector
from ..nested.flattener import NestedTspanFlattener

logger = logging.getLogger(__name__)


def fix_nested_in_file(
    source: Path | str,
    dest: Path | str,
    *,
    strategy: str = "preserve_style",
    pretty_print: bool = True,
) -> bool:
    """
    Deprecated convenience wrapper.
    Prefer NormalizeTspans inside the preparation pipeline.
    """
    source, dest = Path(source), Path(dest)
    try:
        tree = etree.parse(str(source), etree.XMLParser(remove_blank_text=False))
        root = tree.getroot()
    except (etree.XMLSyntaxError, OSError) as exc:
        logger.error("Failed to parse %s: %s", source, exc)
        return False

    NestedTspanFlattener(strategy=strategy).process(root)

    dest.write_bytes(
        etree.tostring(root, encoding="utf-8", xml_declaration=True, pretty_print=pretty_print)
    )
    return True
```

#### 4. `nested/__init__.py`

```python
from .detector import NestedTspanDetector
from .flattener import NestedTspanFlattener

__all__ = [
    "NestedTspanDetector",
    "NestedTspanFlattener",
]
# MatchFixNestedTags removed from public exports
```

---

## Part B — `extraction/`

### Current state

| File / symbol | Role | Issues |
|---------------|------|--------|
| `extractor.py` → `SVGTranslationExtractor` | Main extraction | Owns header logic inline |
| `extractor.py` → `_extract_header_mapping` | Header-only switches | Buried private method; hard to test/reuse |
| `strategies.py` | Matching strategies | Good, keep |
| `header_adder.py` | (user-added / planned) | Name implies “add”; logic is extract; may duplicate switch processing |

### Target design

```text
extraction/
  extractor.py           # SVGTranslationExtractor (orchestration only)
  header.py              # NEW – HeaderMappingExtractor
  strategies.py          # unchanged
  switch_collector.py    # NEW (optional) – shared per-switch collection
  __init__.py
```

No injection/adding logic belongs here.

---

### Proposed new / modified classes

#### 1. `SwitchTranslationCollector` (optional shared helper)

**File:** `extraction/switch_collector.py`

Extracts the per-switch logic currently in `_process_switch` so both full extraction and header extraction reuse it.

```python
# extraction/switch_collector.py
from __future__ import annotations

from ..config import TranslationConfig
from ..core import SwitchNode, TextNode
from ..core.mapping import TranslationMapping
from ..utils.text import normalize_text
from .strategies import MatchingStrategy


class SwitchTranslationCollector:
    """Collect translations from one <switch> into a TranslationMapping."""

    def __init__(
        self,
        config: TranslationConfig,
        strategy: MatchingStrategy,
    ) -> None:
        self.config = config
        self.strategy = strategy

    def collect(self, switch: SwitchNode, mapping: TranslationMapping) -> None:
        default = switch.default_text_node()
        if default is None:
            return

        default_texts = default.texts(
            normalize=True,
            case_insensitive=self.config.case_insensitive,
        )
        if not any(default_texts):
            return

        for tspan in default.tspans():
            tid = tspan.get("id")
            if tid and tspan.text and tspan.text.strip():
                mapping.tspans_by_id[tid] = tspan.text.strip()

        for x in default_texts:
            key = normalize_text(x, self.config.case_insensitive)
            mapping.new.setdefault(key, {})

        for node in switch.text_nodes():
            if node.is_fallback or not node.language:
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
                    node.language,
                    m.translated_text,
                    case_insensitive=False,
                )
```

#### 2. `HeaderMappingExtractor` (replaces header_adder / private method)

**File:** `extraction/header.py`

```python
# extraction/header.py
from __future__ import annotations

from lxml import etree

from ..config import TranslationConfig
from ..core import SwitchNode
from ..core.mapping import TranslationMapping
from .strategies import ByTspanIdStrategy, MatchingStrategy
from .switch_collector import SwitchTranslationCollector

SVG_NS = {"svg": "http://www.w3.org/2000/svg"}


class HeaderMappingExtractor:
    """
    Extract translations only from header switches:
    //svg:g[@id='header']//svg:switch[not(ancestor::svg:g[@id='subtitle'])]
    """

    def __init__(
        self,
        config: TranslationConfig | None = None,
        strategy: MatchingStrategy | None = None,
    ) -> None:
        self.config = config or TranslationConfig()
        self.strategy = strategy or ByTspanIdStrategy()
        self.collector = SwitchTranslationCollector(self.config, self.strategy)

    def extract(self, root: etree._Element) -> dict[str, dict[str, str]]:
        switches = root.xpath(
            "//svg:g[@id='header']//svg:switch[not(ancestor::svg:g[@id='subtitle'])]",
            namespaces=SVG_NS,
        )
        if not switches:
            return {}

        mapping = TranslationMapping()
        for el in switches:
            self.collector.collect(SwitchNode(el), mapping)

        return mapping.new
```

#### 3. `SVGTranslationExtractor` (slim orchestration)

**File:** `extraction/extractor.py` (key parts)

```python
class SVGTranslationExtractor:
    def __init__(
        self,
        config: TranslationConfig | None = None,
        matching_strategy: MatchingStrategy | None = None,
    ) -> None:
        self.config = config or TranslationConfig()
        self.year_handler = YearTitleHandler(self.config)
        self.strategy = matching_strategy or ByTspanIdStrategy()
        self.collector = SwitchTranslationCollector(self.config, self.strategy)
        self.header_extractor = HeaderMappingExtractor(self.config, self.strategy)

    def extract_from_root(self, root: etree._Element) -> TranslationMapping:
        mapping = TranslationMapping()

        for switch_el in root.xpath("//svg:switch", namespaces=SVG_NS):
            self.collector.collect(SwitchNode(switch_el), mapping)

        if self.config.enable_year_titles and mapping.new:
            self.year_handler.build_templates(mapping)

        header = self.header_extractor.extract(root)
        if header:
            mapping.meta["header"] = header

        return mapping

    # extract() / extract_json() remain as today (load via SvgDocument, then extract_from_root)
```

#### 4. `extraction/__init__.py`

```python
from .extractor import SVGTranslationExtractor
from .header import HeaderMappingExtractor
from .strategies import (
    ByPositionStrategy,
    ByTspanIdStrategy,
    CompositeMatchingStrategy,
    MatchingStrategy,
)
from .switch_collector import SwitchTranslationCollector

__all__ = [
    "ByPositionStrategy",
    "ByTspanIdStrategy",
    "CompositeMatchingStrategy",
    "HeaderMappingExtractor",
    "MatchingStrategy",
    "SVGTranslationExtractor",
    "SwitchTranslationCollector",
]
```

#### 5. About `header_adder.py`

- **Do not keep** a module named `header_adder` under `extraction/`.
- If the file already exists, rename/move its logic into `header.py` as `HeaderMappingExtractor`.
- Any logic that *writes* header content belongs in `injection/`, not here.

---

## Part C — Implementation Plan (English)

### Phase 0 – Baseline (½ day)
- Branch: `refactor/nested-extraction`.
- Freeze current behaviour with fixture SVGs:
  - nested tspans (raise / flatten / preserve_style)
  - normal switches
  - header + subtitle switches
  - files that currently go through `MatchFixNestedTags`
- Record extract JSON and (if used) fixed-file outputs as golden samples.

### Phase 1 – `nested/` cleanup (1 day)
1. Confirm `NormalizeTspans` is the only in-pipeline consumer of `NestedTspanFlattener`.
2. Remove `MatchFixNestedTags` from `nested/__init__.py` public exports.
3. Either:
   - **A:** Delete `fixer.py`, or
   - **B:** Move a thin `fix_nested_in_file` helper to `legacy/` (or a `tools/` script).
4. Keep `detector.py` / `flattener.py` API stable.
5. Run nested-related fixtures; behaviour must match golden samples.

### Phase 2 – Shared collector (1 day)
1. Add `extraction/switch_collector.py` with `SwitchTranslationCollector`.
2. Point `SVGTranslationExtractor._process_switch` at the collector (or replace the method entirely).
3. Re-run full-extraction fixtures; JSON output must be identical.

### Phase 3 – Header extraction (1 day)
1. Add `extraction/header.py` with `HeaderMappingExtractor`.
2. Replace `_extract_header_mapping` in the extractor with a call to `HeaderMappingExtractor`.
3. If `header_adder.py` exists, migrate any useful code then delete/rename the file.
4. Assert `mapping.meta["header"]` matches previous output on header fixtures.

### Phase 4 – Package surface & docs (½ day)
1. Update `extraction/__init__.py` and `nested/__init__.py` exports.
2. Update top-level package `__init__.py` if it re-exported `MatchFixNestedTags` (deprecate or remove).
3. Short notes in package READMEs:
   - nested: Detector + Flattener only; fixing is done via preparation.
   - extraction: HeaderMappingExtractor + SwitchTranslationCollector responsibilities.
4. PR with before/after fixture diffs.

### Phase 5 – Verification checklist
- [ ] Valid SVGs: extract JSON unchanged
- [ ] Header-only mapping unchanged under `meta["header"]`
- [ ] Nested strategies still behave as before inside preparation
- [ ] No remaining imports of `MatchFixNestedTags` in core paths
- [ ] No module named `header_adder` under `extraction/`
- [ ] Legacy helper (if kept) emits `DeprecationWarning`

### Risk notes
- **Header XPath** is domain-specific (`id='header'` / `id='subtitle'`). Keep it isolated in `HeaderMappingExtractor` so the core extractor stays generic.
- **Removing fixer** may break external scripts that imported `MatchFixNestedTags`. Mitigate with a deprecated legacy wrapper for one release.
- **Collector extraction** is a pure move of logic; avoid behaviour tweaks in the same PR.

### Success criteria
- `nested` public API = detector + flattener only.
- Header extraction is a dedicated, testable class.
- Per-switch collection is shared and unit-testable without full file I/O.
- No functional regressions on golden fixtures.

---

### Suggested order relative to preparation work

```text
1. preparation/steps refactor   (already drafted)
2. nested cleanup               (this plan, Phase 1)
3. extraction collector+header  (this plan, Phases 2–3)
4. integration test pass across all three areas
```

This keeps dependency direction clean: `preparation` → `nested.flattener`; `extraction` stays independent of preparation.
