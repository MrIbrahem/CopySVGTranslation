**New Injection Design**  
(How the large `work_on_switches` is broken down)

In the current code, `work_on_switches` does too many things at once:

- Finds the default (fallback) text node  
- Builds available translations (including year-title logic)  
- Decides whether to skip / update / insert  
- Clones nodes and tspans  
- Generates IDs  
- Writes the translated text  
- Updates stats  

In the new design this responsibility is split into clear, testable pieces.

---

### Target structure (injection/)

```
injection/
├── __init__.py
├── preparer.py              # SvgPreparationPipeline
├── injector.py              # SVGTranslationInjector (orchestrator only)
├── id_manager.py            # IdManager
├── switch_processor.py      # SwitchProcessor  ← replaces most of work_on_switches
├── translation_applier.py   # TranslationApplier
└── steps/                   # Preparation only (runs before injection)
    ├── base.py
    ├── load.py
    ├── validate.py
    ├── normalize_tspans.py
    ├── assign_ids.py
    ├── split_languages.py
    └── reorder.py
```

---

### Responsibilities

| Component | Role |
|-----------|------|
| **SvgPreparationPipeline** | Runs the `steps/` pipeline once. Guarantees a clean, well-structured SVG (every text inside a switch, tspans present, IDs assigned, languages split, ordered). |
| **IdManager** | Single source of truth for generating and tracking unique IDs. |
| **SwitchProcessor** | Iterates over all `<switch>` elements and coordinates the work for one switch. |
| **TranslationApplier** | Pure logic: given a default node + mapping + language → produce the new/updated `<text>` node. |
| **SVGTranslationInjector** | Thin orchestrator: prepare → process switches → fix/sort → collect stats → optionally save. |

---

### Key classes (sketch)

#### 1. `IdManager`

```python
# injection/id_manager.py
class IdManager:
    def __init__(self, existing_ids: set[str] | None = None): ...
    def register(self, id_: str) -> None: ...
    def allocate_trsvg(self) -> str: ...
    def allocate_clone(self, base_id: str | None, lang: str) -> str: ...
    def allocate_for_tspan(self, original_id: str | None, lang: str) -> str: ...
```

#### 2. `TranslationApplier`

```python
# injection/translation_applier.py
@dataclass
class ApplyResult:
    action: Literal["inserted", "updated", "skipped"]
    node: etree._Element | None = None   # new or updated node

class TranslationApplier:
    def __init__(self, config: TranslationConfig, id_manager: IdManager): ...

    def apply_language(
        self,
        default_node: etree._Element,
        default_texts: list[str],
        lang: str,
        translations: Mapping[str, str],   # lang → text for each line
        existing_lang_node: etree._Element | None,
    ) -> ApplyResult:
        """
        - If existing_lang_node and not overwrite → skipped
        - If existing_lang_node and overwrite → update tspans in place
        - Else → clone default_node, set systemLanguage, fill translations, new IDs
        """
```

This class contains the core logic that used to live inside the nested loops of `work_on_switches`.

#### 3. `SwitchProcessor`

```python
# injection/switch_processor.py
class SwitchProcessor:
    def __init__(
        self,
        config: TranslationConfig,
        id_manager: IdManager,
        applier: TranslationApplier,
        year_handler: YearTitleHandler | None = None,
    ): ...

    def process(
        self,
        switch: etree._Element,
        mapping: TranslationMapping,
        stats: InjectorStats,
    ) -> None:
        """
        1. Find fallback (default) <text> node
        2. Extract default_texts
        3. Enrich mapping with year-title expansions (if enabled)
        4. Collect existing languages in this switch
        5. For every language present in the mapping:
              - decide skip / update / insert
              - call TranslationApplier
              - update stats
        6. Optionally re-sort children of the switch
        """
```

#### 4. `SVGTranslationInjector` (new, thin)

```python
# injection/injector.py
class SVGTranslationInjector:
    def __init__(self, config: TranslationConfig):
        self.config = config
        self.id_manager = IdManager()
        self.applier = TranslationApplier(config, self.id_manager)
        self.switch_processor = SwitchProcessor(
            config, self.id_manager, self.applier, YearTitleHandler(config)
        )
        self.preparer = SvgPreparationPipeline(config)

    def inject(
        self,
        svg_path: Path,
        mapping: TranslationMapping,
        *,
        target_path: Path | None = None,
        save: bool = False,
    ) -> tuple[etree._ElementTree | None, InjectorStats]:
        stats = InjectorStats()

        # 1. Prepare (pipeline)
        tree, root = self.preparer.run(svg_path)
        if tree is None:
            stats.error = "preparation_failed"
            return None, stats

        # 2. Snapshot languages before
        before = tree_langs(tree)
        stats.languages_before = sorted(before)

        # 3. Seed IdManager with existing IDs
        self.id_manager.register_many(root.xpath("//@id"))

        # 4. Process every switch
        for switch in root.xpath("//svg:switch", namespaces=SVG_NS):
            self.switch_processor.process(switch, mapping, stats)

        # 5. Final housekeeping
        self._finalize_switches(root)

        # 6. Languages after + stats
        after = tree_langs(tree)
        stats.languages_after = sorted(after - before)
        stats.all_languages = len(after)
        stats.new_languages = len(after - before)

        # 7. Save if requested
        if save and target_path:
            self._save(tree, target_path)

        return tree, stats

    def prepare(self, svg_path: Path) -> etree._ElementTree:
        """Public helper used by service.prepare_only()."""
        tree, _ = self.preparer.run(svg_path)
        return tree
```

---

### Preparation pipeline (`steps/`) – runs **before** any injection

```python
# injection/preparer.py
class SvgPreparationPipeline:
    def __init__(self, config: TranslationConfig):
        self.steps = [
            LoadDocument(config),
            ValidateStructure(config),
            NormalizeTspans(config),      # uses NestedTspanFlattener according to config.nested_strategy
            AssignIds(config),
            SplitLanguages(config),
            ReorderTexts(config),
        ]

    def run(self, path: Path) -> tuple[etree._ElementTree, etree._Element]:
        ctx = PreparationContext(path=path, config=self.config)
        for step in self.steps:
            step.execute(ctx)
        return ctx.tree, ctx.root
```

Each step is small and focused:

| Step | Old location | New job |
|------|----------------|---------|
| `LoadDocument` | `_load_document` | Parse + ensure namespace |
| `ValidateStructure` | `_check_style_elements`, `_check_no_trefs`, nested check | Raise structured errors |
| `NormalizeTspans` | `_wrap_loose_text...` + nested handling | Guarantee every text piece is in a tspan |
| `AssignIds` | `_assign_missing_ids` + IdManager | All translatable nodes have stable IDs |
| `SplitLanguages` | `_split_switch_languages` | One language per `<text>` |
| `ReorderTexts` | `_reorder_texts` | Deterministic order (fallback last) |

---

### Flow overview

```
SVG file
   │
   ▼
SvgPreparationPipeline          ← steps/ (structure only)
   │
   ▼
Clean <switch> tree
   │
   ▼
SVGTranslationInjector.inject()
   │
   ├─► IdManager (seeded)
   │
   └─► for each switch:
           SwitchProcessor.process()
               │
               ├─ find default node + texts
               ├─ year-title enrichment
               └─ for each language:
                      TranslationApplier.apply_language()
                           ├─ skip
                           ├─ update in place
                           └─ insert clone + new IDs
   │
   ▼
Stats + optional save
```

---

### Benefits of this split

1. **`work_on_switches` disappears** – its logic lives in `SwitchProcessor` + `TranslationApplier`.
2. **Testability** – you can unit-test `TranslationApplier` with a single default node and a dict of translations; no full SVG needed.
3. **Single responsibility** – preparation is completely separate from translation application.
4. **ID logic centralized** – no more duplicated ID generation between preparer and injector.
5. **Config-driven** – overwrite, nested strategy, year handling, etc. all flow from `TranslationConfig`.
6. **Easy to extend** – new behaviour (e.g. “only inject certain languages”) becomes a filter inside `SwitchProcessor` or a new strategy class.

---

### Minimal public surface of the injection package

```python
# injection/__init__.py
from .injector import SVGTranslationInjector
from .preparer import SvgPreparationPipeline
from .id_manager import IdManager

__all__ = ["SVGTranslationInjector", "SvgPreparationPipeline", "IdManager"]
```

Everything else (`SwitchProcessor`, `TranslationApplier`, steps) stays internal.

This design keeps the injector itself small and readable while giving each former responsibility of `work_on_switches` a clear, modern home.
