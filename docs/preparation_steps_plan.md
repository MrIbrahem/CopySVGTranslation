# Draft: `preparation/steps` Refactor

Scope: **preparation/steps only**

---

## 1. Target Pipeline Order

```text
LoadDocument
ValidateStructure          # existing structural checks
ValidateSwitchLanguages    # NEW – extracted validation
NormalizeTspans            # nested strategy + wrap loose text only
AssignIds                  # allocate missing IDs + clean existing IDs
RemoveEmptyNodes           # NEW – was part of WrapTspans
WrapTextElements
SplitLanguages             # split/clone only (no heavy validation)
ReorderTexts
```

---

## 2. New / Modified Classes

### 2.1 `ValidateSwitchLanguages` (new)

**File:** `preparation/steps/validate_switch.py`

```python
# preparation/steps/validate_switch.py
from __future__ import annotations

from lxml import etree

from ...exceptions import SvgStructureError
from ...utils import split_lang_list
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class ValidateSwitchLanguages(PreparationStep):
    """
    Early structural + language validation for every <switch>.

    Responsibilities (read-only):
    - Reject non-<text> children
    - Reject non-whitespace text content outside <text>
    - Reject duplicate languages inside one <text>
    - Reject the same language declared by two different <text> nodes
      (including the implicit "fallback")
    """

    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        for switch in ctx.root.findall(f".//{{{SVG_NS}}}switch"):
            self._validate_switch(switch)

    def _validate_switch(self, switch: etree._Element) -> None:
        existing_langs: set[str] = set()

        for child in list(switch):
            # Non-element nodes (comments, etc.)
            if not isinstance(child.tag, str):
                if child.text and child.text.strip():
                    raise SvgStructureError(
                        code="structure-error-switch-text-content-outside-text",
                        element=switch,
                    )
                continue

            if child.tag not in (f"{{{SVG_NS}}}text", "text"):
                raise SvgStructureError(
                    code="structure-error-switch-child-not-text",
                    element=child,
                )

            sys_lang = child.get("systemLanguage")
            real_langs = split_lang_list(sys_lang) or ["fallback"]

            seen_in_this_text: set[str] = set()
            for lang in real_langs:
                if lang in seen_in_this_text:
                    raise SvgStructureError(
                        code="structure-error-multiple-lang-in-text",
                        extra=[lang],
                        element=child,
                    )
                seen_in_this_text.add(lang)

                if lang in existing_langs:
                    raise SvgStructureError(
                        code="structure-error-multiple-text-same-lang",
                        extra=[lang],
                        element=child,
                    )

            existing_langs.update(seen_in_this_text)


__all__ = ["ValidateSwitchLanguages"]
```

---

### 2.2 `RemoveEmptyNodes` (new – extracted from `WrapTspans`)

**File:** `preparation/steps/remove_empty_nodes.py`

```python
# preparation/steps/remove_empty_nodes.py
from __future__ import annotations

from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class RemoveEmptyNodes(PreparationStep):
    """
    Drop empty <text> and <tspan> nodes (no children and no text).
    Must run after ID assignment so we can unregister IDs cleanly.
    """

    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        if ctx.id_manager is None:
            raise ValueError("id_manager is not set")

        candidates = (
            ctx.root.findall(f".//{{{SVG_NS}}}tspan")
            + ctx.root.findall(f".//{{{SVG_NS}}}text")
        )

        for node in list(candidates):
            if list(node) or node.text:
                continue

            node_id = node.get("id")
            if node_id:
                ctx.id_manager.existing_ids.discard(node_id)

            parent = node.getparent()
            if parent is not None:
                parent.remove(node)


__all__ = ["RemoveEmptyNodes"]
```

---

### 2.3 `NormalizeTspans` (slimmed)

**File:** `preparation/steps/normalize_tspans.py`  
**Change:** Keep only nested handling + wrapping of loose text.  
**Remove:** the entire `WrapTspans` class.

```python
# preparation/steps/normalize_tspans.py
from __future__ import annotations

from lxml import etree

from ...nested import NestedTspanFlattener
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class NormalizeTspans(PreparationStep):
    """
    1. Apply nested-tspan strategy (via NestedTspanFlattener).
    2. Wrap loose text / tails under <text> into <tspan>.
    """

    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        flattener = NestedTspanFlattener(self.config.nested_strategy)
        flattener.process(ctx.root)

        for text_el in ctx.root.findall(f".//{{{SVG_NS}}}text"):
            self._wrap_loose_text(text_el)

    def _wrap_loose_text(self, text_el: etree._Element) -> None:
        children = list(text_el)

        if not children:
            if text_el.text and text_el.text.strip():
                tspan = etree.Element(f"{{{SVG_NS}}}tspan")
                tspan.text = text_el.text
                text_el.text = None
                text_el.append(tspan)
            return

        if text_el.text and text_el.text.strip():
            tspan = etree.Element(f"{{{SVG_NS}}}tspan")
            tspan.text = text_el.text
            text_el.text = None
            text_el.insert(0, tspan)

        for child in children:
            if child.tail and child.tail.strip():
                new_tspan = etree.Element(f"{{{SVG_NS}}}tspan")
                new_tspan.text = child.tail
                child.tail = None
                idx = text_el.index(child)
                text_el.insert(idx + 1, new_tspan)


__all__ = ["NormalizeTspans"]
```

---

### 2.4 `AssignIds` (enhanced – absorbs ID cleaning)

**File:** `preparation/steps/assign_ids.py`

```python
# preparation/steps/assign_ids.py
from __future__ import annotations

import re

from ...exceptions import SvgInvalidIdError, SvgStructureError
from ...utils import collect_ids
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class AssignIds(PreparationStep):
    """
    - Register all existing IDs.
    - Normalize / validate existing IDs on translatable nodes.
    - Allocate missing trsvgN IDs when config.assign_missing_ids is True.
    """

    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        if ctx.id_manager is None:
            raise ValueError("id_manager is not set")

        existing = collect_ids(ctx.root)
        ctx.id_manager.register_many(existing)

        # Reject completely empty id attributes
        for element in ctx.root.xpath("//*[@id]"):
            el_id = element.get("id")
            if not el_id or not el_id.strip():
                raise SvgInvalidIdError(
                    code="structure-error-invalid-node-id",
                    element=element,
                )

        self._clean_existing_ids(ctx)

        if self.config.assign_missing_ids:
            self._assign_missing(ctx)

    def _clean_existing_ids(self, ctx: PreparationContext) -> None:
        assert ctx.id_manager is not None and ctx.root is not None

        nodes = (
            ctx.root.findall(f".//{{{SVG_NS}}}tspan")
            + ctx.root.findall(f".//{{{SVG_NS}}}text")
        )

        for node in nodes:
            node_id = node.get("id")
            if node_id is None:
                continue

            original = node_id
            node_id = node_id.strip()

            if node_id != original:
                ctx.id_manager.existing_ids.discard(original)

            if not node_id:
                node.attrib.pop("id", None)
                continue

            if "|" in node_id or "/" in node_id:
                raise SvgStructureError(code="structure-error-invalid-node-id")

            # Pure numeric IDs are not useful – drop them
            if node_id.isdigit():
                node.attrib.pop("id", None)
                ctx.id_manager.existing_ids.discard(node_id)
                continue

            node.set("id", node_id)
            ctx.id_manager.register(node_id)

    def _assign_missing(self, ctx: PreparationContext) -> None:
        assert ctx.id_manager is not None and ctx.root is not None

        for text_el in ctx.root.findall(f".//{{{SVG_NS}}}text"):
            if not text_el.get("id"):
                text_el.set("id", ctx.id_manager.allocate_trsvg())

            for tspan in text_el.findall(f"./{{{SVG_NS}}}tspan"):
                if not tspan.get("id"):
                    tspan.set("id", ctx.id_manager.allocate_trsvg())


__all__ = ["AssignIds"]
```

---

### 2.5 `SplitLanguages` (slimmed – validation removed)

**File:** `preparation/steps/split_languages.py`

```python
# preparation/steps/split_languages.py
from __future__ import annotations

import copy
import re

from lxml import etree

from ...utils import split_lang_list
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


def _clone_element(el: etree._Element) -> etree._Element:
    return copy.deepcopy(el)


class SplitLanguages(PreparationStep):
    """
    Expand comma-separated systemLanguage values into separate <text> nodes.
    Assumes ValidateSwitchLanguages has already run (no structural checks here).
    """

    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        for switch in ctx.root.findall(f".//{{{SVG_NS}}}switch"):
            self._split_languages_in_switch(switch, ctx)

    def _split_languages_in_switch(
        self,
        switch: etree._Element,
        ctx: PreparationContext,
    ) -> None:
        for text_el in list(switch):
            if not isinstance(text_el.tag, str):
                continue
            if text_el.tag not in (f"{{{SVG_NS}}}text", "text"):
                continue

            sys_lang = text_el.get("systemLanguage")
            real_langs = split_lang_list(sys_lang) or ["fallback"]

            if len(real_langs) == 1:
                self._apply_single_lang(text_el, real_langs[0])
                continue

            # Keep first language on the original node
            self._apply_single_lang(text_el, real_langs[0])

            parent_list = list(switch)
            index = parent_list.index(text_el)

            for extra_lang in real_langs[1:]:
                cloned = _clone_element(text_el)
                self._apply_single_lang(cloned, extra_lang)
                self._reassign_ids(cloned, ctx)
                switch.insert(index + 1, cloned)
                index += 1

    @staticmethod
    def _apply_single_lang(text_el: etree._Element, lang: str) -> None:
        if lang == "fallback":
            text_el.attrib.pop("systemLanguage", None)
        else:
            text_el.set("systemLanguage", lang)

    def _reassign_ids(self, element: etree._Element, ctx: PreparationContext) -> None:
        if ctx.id_manager is None:
            return

        el_id = element.get("id")
        if el_id and re.match(r"^trsvg[0-9]+$", el_id):
            el_id = None

        if el_id:
            new_id = ctx.id_manager.allocate_clone(
                el_id, element.get("systemLanguage", "")
            )
        else:
            new_id = ctx.id_manager.allocate_trsvg()

        element.set("id", new_id)


__all__ = ["SplitLanguages"]
```

---

### 2.6 Package exports & pipeline wiring

**File:** `preparation/steps/__init__.py`

```python
from .assign_ids import AssignIds
from .base import PreparationContext, PreparationStep
from .load import LoadDocument
from .normalize_tspans import NormalizeTspans
from .remove_empty_nodes import RemoveEmptyNodes
from .reorder import ReorderTexts
from .split_languages import SplitLanguages
from .validate import ValidateStructure
from .validate_switch import ValidateSwitchLanguages
from .wrap_text_elements import WrapTextElements

__all__ = [
    "AssignIds",
    "LoadDocument",
    "NormalizeTspans",
    "PreparationContext",
    "PreparationStep",
    "RemoveEmptyNodes",
    "ReorderTexts",
    "SplitLanguages",
    "ValidateStructure",
    "ValidateSwitchLanguages",
    "WrapTextElements",
]
```

**File:** `preparation/preparer.py` (pipeline list only)

```python
self.steps: list[PreparationStep] = [
    LoadDocument(config),
    ValidateStructure(config),
    ValidateSwitchLanguages(config),   # NEW
    NormalizeTspans(config),
    AssignIds(config),
    RemoveEmptyNodes(config),          # NEW (replaces WrapTspans)
    WrapTextElements(config),
    SplitLanguages(config),
    ReorderTexts(config),
]
```

---

## 3. Implementation Plan (English)

### Phase 0 – Preparation (½ day)
- Create a feature branch: `refactor/preparation-steps-split`.
- Ensure existing unit / integration tests (if any) pass on `main` so you have a baseline.
- Snapshot a few representative SVGs (with nested tspans, multi-lang switches, empty nodes, missing IDs) as golden fixtures.

### Phase 1 – Additive, non-breaking (1–2 days)
1. Add `validate_switch.py` with `ValidateSwitchLanguages` (copy logic from current `_validate_switch_languages`).
2. Add `remove_empty_nodes.py` with `RemoveEmptyNodes` (copy empty-node logic from `WrapTspans`).
3. Wire both into `steps/__init__.py` and into the pipeline **in addition to** the old code (temporary duplication is OK).
4. Run the fixture SVGs through `SvgPreparationPipeline` and confirm behaviour is unchanged.

### Phase 2 – Slim existing classes (1 day)
1. Remove the heavy validation body from `SplitLanguages`; keep only split/clone + ID reassignment.
2. Move ID-cleaning logic from `WrapTspans` into `AssignIds._clean_existing_ids`.
3. Delete the `WrapTspans` class from `normalize_tspans.py`.
4. Update `preparer.py` to the final step order shown above.
5. Update `steps/__init__.py` (drop `WrapTspans`).

### Phase 3 – Verification (1 day)
- Re-run all fixtures; compare trees before/after (normalize whitespace if needed).
- Manually test edge cases:
  - Duplicate language in one switch
  - Comma-separated `systemLanguage`
  - Empty `<tspan>` / `<text>`
  - Numeric-only or `|`/`/` IDs
  - Missing IDs with `assign_missing_ids=True/False`
- Fix any regressions.

### Phase 4 – Cleanup & docs (½ day)
- Remove any dead imports / commented code left from `WrapTspans`.
- Add short docstrings noting the new single-responsibility boundaries.
- Update the preparation README (or internal notes) with the new pipeline order.
- Open PR with a clear description of responsibility split and the new step list.

### Risk notes
- **Order sensitivity:** `RemoveEmptyNodes` must stay after `AssignIds` so IDs can be unregistered.
- **Validation timing:** Moving checks earlier may surface errors that previously appeared only during split; that is intentional and desirable.
- **Deep copy cost:** Unchanged in this phase; leave clone performance for a later pass.

### Success criteria
- No behavioural change on valid SVGs.
- Invalid switch language configurations fail in `ValidateSwitchLanguages` with the same error codes as before.
- `WrapTspans` no longer exists; its duties are clearly owned by `AssignIds` + `RemoveEmptyNodes`.
- `SplitLanguages` contains no structural validation logic.
