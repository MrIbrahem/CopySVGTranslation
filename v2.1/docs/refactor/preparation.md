**Preparation in the New Design**

Preparation is the stage that makes an SVG safe and consistent **before** any translations are injected. Its only goal is:

> Guarantee that the SVG is in a standard, translation-ready form.

After the pipeline finishes we have:

-   Every `<text>` lives inside a `<switch>`
-   Every piece of translatable text is wrapped in a `<tspan>`
-   No unsupported nested `<tspan>`s (or they have been handled according to the configured strategy)
-   Every translatable node has a unique `id`
-   `systemLanguage` values are normalized and split (one language per `<text>`)
-   Children of every `<switch>` are in a deterministic order (fallback last)

---

### Structure

```
├── copy_svg_translation/
│   ├── preparation/
│   │   ├── steps/                   # Preparation only (runs before injection)
│   │   │   ├── __init__.py
│   │   │   ├── assign_ids.py
│   │   │   ├── base.py
│   │   │   ├── load.py
│   │   │   ├── normalize_tspans.py
│   │   │   ├── reorder.py
│   │   │   ├── split_languages.py
│   │   │   └── validate.py
│   │   ├── __init__.py
│   │   └── preparer.py                # SvgPreparationPipeline
```

### Responsibilities

| Component                  | Role                                                                                                                                                           |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **SvgPreparationPipeline** | Runs the `steps/` pipeline once. Guarantees a clean, well-structured SVG (every text inside a switch, tspans present, IDs assigned, languages split, ordered). |

---

### Core Components

#### 1. `PreparationContext` (shared state between steps)

```python
@dataclass
class PreparationContext:
    path: Path
    config: TranslationConfig
    tree: etree._ElementTree | None = None
    root: etree._Element | None = None
    id_manager: IdManager | None = None
    translatable_nodes: list[etree._Element] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
```

Each step reads from and writes to this context.

#### 2. `PreparationStep` (base class)

```python
# steps/base.py
class PreparationStep(ABC):
    def __init__(self, config: TranslationConfig) -> None:
        self.config = config

    @abstractmethod
    def execute(self, ctx: PreparationContext) -> None:
        """Modify ctx in-place. Raise on fatal errors."""
        ...
```

#### 3. `SvgPreparationPipeline`

```python
# preparer.py
class SvgPreparationPipeline:
    def __init__(self, config: TranslationConfig) -> None:
        self.config = config
        self.steps: list[PreparationStep] = [
            LoadDocument(config),
            ValidateStructure(config),
            NormalizeTspans(config),
            AssignIds(config),
            SplitLanguages(config),
            ReorderTexts(config),
        ]

    def run(self, path: Path) -> tuple[etree._ElementTree[etree._Element], etree._Element]:
        ctx = PreparationContext(
            path=path,
            config=self.config,
            id_manager=IdManager(),
        )
        for step in self.steps:
            step.execute(ctx)
        return ctx.tree, ctx.root
```

---

### Step Details

| Step                  | File                  | Responsibility                                                                                                                             | Old code it replaces                                                      |
| --------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| **LoadDocument**      | `load.py`             | Parse the file, ensure a root element and a sane default namespace                                                                         | `_load_document`                                                          |
| **ValidateStructure** | `validate.py`         | Reject `<tref>`, overly complex CSS with `#`, texts containing `$N`, and nested tspans according to `config.nested_strategy`               | `_check_style_elements`, `_check_no_trefs`, part of nested checks         |
| **NormalizeTspans**   | `normalize_tspans.py` | Wrap loose text into `<tspan>`, handle nested elements (`split_nested_tspans`, `preserve_style` / `flatten` / `raise`), remove empty nodes | `_wrap_loose_text_into_tspans` + nested flattener                         |
| **AssignIds**         | `assign_ids.py`       | Collect existing IDs, assign `trsvgN` to nodes that lack an id, clean invalid IDs                                                          | `_collect_existing_ids` + `_assign_missing_ids` + part of `_clean_ids...` |
| **SplitLanguages**    | `split_languages.py`  | Expand `systemLanguage="ar,fr"` into separate `<text>` nodes with new IDs                                                                  | `_split_switch_languages`                                                 |
| **ReorderTexts**      | `reorder.py`          | Deterministically order children of every `<switch>` (languages first, fallback last)                                                      | `_reorder_texts`                                                          |

---

### Example Step Implementation

```python
# steps/normalize_tspans.py
class NormalizeTspans(PreparationStep):
    def execute(self, ctx: PreparationContext) -> None:
        flattener = NestedTspanFlattener(self.config.nested_strategy)

        # 1. Handle nested tspans first
        flattener.process(ctx.root)

        # 2. Wrap any loose text inside <text>
        for text in ctx.root.findall(f".//{{{SVG_NS}}}text"):
            self._wrap_loose_text(text)

        # 3. Rebuild the list of translatable nodes
        ctx.translatable_nodes = (
            ctx.root.findall(f".//{{{SVG_NS}}}tspan")
            + ctx.root.findall(f".//{{{SVG_NS}}}text")
        )
```

---

### How It Connects to the Injector

```python
# Inside SVGTranslationInjector.inject()
tree, root = self.preparer.run(svg_path)   # ← full pipeline

# Only after preparation do we start injecting
self.id_manager.register_many(...)         # uses IDs assigned by AssignIds
for switch in root.xpath("//svg:switch", ...):
    self.switch_processor.process(switch, mapping, stats)
```

-   Preparation knows **nothing** about translations.
-   Injection **assumes** the SVG is already clean and does not repeat preparation work.

---

### Benefits

1. Each step is small and independently testable.
2. Steps can later be reordered or disabled via config if needed.
3. Nested-tspan handling becomes an official part of `NormalizeTspans` instead of an external utility.
4. `IdManager` is created early and shared with the injector — no duplicated ID logic.
5. `service.prepare_only()` can clean an SVG without injecting any translations.

---

### Flow Summary

```
Raw SVG
  │
  ▼
LoadDocument
  │
  ▼
ValidateStructure          ← fail fast on unsupported files
  │
  ▼
NormalizeTspans            ← most important step (nested + loose text)
  │
  ▼
AssignIds
  │
  ▼
SplitLanguages
  │
  ▼
ReorderTexts
  │
  ▼
Translation-ready SVG  →  SwitchProcessor + TranslationApplier
```

This keeps Preparation clean, maintainable, and completely separate from the injection logic that used to be piled into `work_on_switches`.
