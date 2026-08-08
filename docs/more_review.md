# Analytical Report & Recommendations

**Subjects**
1. `CopySVGTranslation/extraction/header_adder.py` (the implementation you provided)
2. `MatchFixNestedTags` used as an independent service
3. How to integrate nested-tag analysis & repair into the main `SVGTranslationService`

---

## 1. `extraction/header_adder.py`

### What the code actually does

Despite the filename, this module does **not** handle SVG header groups (`<g id="header">`). It performs year-pattern stripping on title translations:

| Class | Responsibility |
|-------|----------------|
| `ByLanguage` | Language-specific removal of `{year}` (and related suffixes/prefixes) from a single string |
| `TitlesTranslationsRenderer` | Transforms a `title_new`-shaped dict by stripping year patterns from both the English key and each translation |
| `AddTitlesTranslationsFromTitles` | Merges the resulting year-free entries into `mapping.new` (skips keys that already exist) |

In short: it **derives additional plain translations from year-title templates**.

### Problems

| Issue | Detail | Impact |
|-------|--------|--------|
| **Misleading name & location** | Named `header_adder` and placed under `extraction/`, but it only mutates `TranslationMapping.title_new` → `new` | Confuses maintainers; wrong package boundary |
| **Overlap with `YearTitleHandler`** | `titles/year_handler.py` already builds `title_new` and expands concrete years at injection time | Two parallel year-title systems with different rules |
| **Hard-coded language rules** | Special cases only for `abr` and `ja`, plus a small list of comma/year endings | Fragile; every new language needs code changes |
| **Side-effecting API** | `run()` mutates `mapping.new` in place and only exposes a boolean `changes` | Harder to test and reason about |
| **Incomplete pattern coverage** | Many real-world year placements will be missed or mishandled | Silent incorrect keys or missing entries |
| **No config integration** | Ignores `TranslationConfig.enable_year_titles` | Behaviour can diverge from the rest of the library |

### Recommendations

**Priority: High**

1. **Rename and relocate**
   ```text
   # Current
   extraction/header_adder.py

   # Recommended
   titles/year_stripper.py
   # or
   titles/title_expander.py
   ```
   Suggested names:
   - `ByLanguage` → keep as private helper or rename to `YearPatternStripper`
   - `TitlesTranslationsRenderer` → acceptable
   - `AddTitlesTranslationsFromTitles` → `YearFreeTitleMerger` / `TitleNewToNewMerger`

2. **Unify with `YearTitleHandler`**
   - Make this logic a method (or injected collaborator) of `YearTitleHandler`.
   - Single source of truth for:
     - building `{year}` templates
     - expanding templates to concrete years (injection side)
     - optionally stripping `{year}` and merging into `mapping.new`
   - Gate everything behind `config.enable_year_titles`.

3. **Prefer pure / explicit APIs**
   ```python
   def derive_year_free_entries(
       title_new: dict[str, dict[str, str]],
   ) -> dict[str, dict[str, str]]:
       ...

   def merge_year_free_into_new(mapping: TranslationMapping) -> bool:
       """Returns True if mapping.new was modified."""
       ...
   ```
   Avoid silent in-place mutation; either return a new mapping or return a clear change flag.

4. **Replace hard-coded per-language rules**
   - Prefer a small, data-driven list of patterns (prefix/suffix) instead of `if lang == "ja"` methods.
   - Fall back to the generic `ends_data` / startswith logic for most languages.
   - Keep language-specific overrides only when the generic rules are insufficient, and document them.

5. **Call site**
   - Invoke the merger once after `YearTitleHandler.build_templates()` inside the extractor (or inside the service after extraction), not as a separate poorly-named “header” step.

---

## 2. `MatchFixNestedTags` as an Independent Service

### Current role

`nested/fixer.py` is a self-contained utility that:

- Loads an SVG from disk
- Detects nested `<tspan>` / `<a>` via `NestedTspanDetector`
- Applies `NestedTspanFlattener`
- Writes a new file
- Tracks how many nested tags existed before the fix

You correctly want to keep it **out of the normal extract/inject path**. That is good design: nested repair is a destructive, opt-in structural change and should not run silently on every translation.

### Strengths of keeping it independent

- Clear separation of concerns
- Safe default behaviour for extract/inject (`nested_strategy="raise"`)
- Can be used as a one-off repair tool or CLI

### Remaining weaknesses

| Issue | Detail |
|-------|--------|
| Mixes I/O with logic | File load + process + save in one class |
| Overlaps `NestedTspanFlattener` | Fixer is mostly a thin I/O wrapper |
| Awkward API | `source_file` / `new_path` can be `None`; error handling is weak |
| Naming | `MatchFixNestedTags` is unclear |

### Recommendations for the standalone service

**Priority: Medium**

1. Keep the **public** entry point simple and explicit:
   ```python
   from CopySVGTranslation.nested import NestedTspanDetector, NestedTspanFlattener
   # or a thin facade
   from CopySVGTranslation import NestedStructureService
   ```

2. Refactor toward a clean service:
   ```python
   class NestedStructureService:
       def __init__(self, strategy: str = "preserve_style", also_fix_a: bool = True): ...

       def analyze(self, source: Path | etree._Element) -> list[...]: ...
       def repair(self, source: Path | etree._Element) -> etree._ElementTree: ...
       def repair_file(self, source: Path, output: Path) -> RepairResult: ...
   ```
   Internally reuse `NestedTspanDetector` + `NestedTspanFlattener`.  
   Deprecate or thin-wrap `MatchFixNestedTags`.

3. Return a structured result (counts, list of fixed nodes, warnings) instead of only a boolean.

---

## 3. Integrating Nested Analysis & Repair into `SVGTranslationService`

You want the main service to **offer** nested-tag analysis/repair without making it part of every extract/inject call.

### Recommended design

Add **explicit, opt-in methods** on `SVGTranslationService` (or a dedicated collaborator it owns). Do **not** run repair automatically inside `extract` / `inject`.

```python
class SVGTranslationService:
    def __init__(self, config: TranslationConfig | None = None) -> None:
        ...
        self._nested = NestedStructureService(
            strategy=self.config.nested_strategy,
            also_fix_a=True,
        )

    # ----- existing API -----
    def extract(...) -> OperationResult[TranslationMapping]: ...
    def inject(...) -> OperationResult[InjectorData]: ...

    # ----- new explicit nested API -----
    def analyze_nested(
        self,
        svg_path: Path | str,
    ) -> OperationResult[list[str]]:
        """Detect nested tspan/a structures. Read-only."""
        ...

    def repair_nested(
        self,
        svg_path: Path | str,
        *,
        output: Path | str | None = None,
        strategy: str | None = None,   # override config if needed
        save: bool = True,
    ) -> OperationResult[etree._ElementTree]:
        """
        Repair nested structures and optionally save.
        Does NOT run as part of extract/inject.
        """
        ...
```

### How it interacts with the existing pipeline

| Mode | Behaviour |
|------|-----------|
| Default extract/inject | Uses `config.nested_strategy`. If `"raise"` → fails fast on nested tags. If `"flatten"` / `"preserve_style"` → `NormalizeTspans` already calls `NestedTspanFlattener` during preparation. |
| Explicit `analyze_nested` | Read-only diagnostics; never mutates. |
| Explicit `repair_nested` | Standalone repair job; writes a cleaned SVG that can later be fed to extract/inject. |

This gives three clear workflows:

```text
1. Strict pipeline (default)
   extract / inject  →  raise on nested tags

2. Lenient pipeline
   config.nested_strategy = "preserve_style"
   extract / inject  →  auto-repair during preparation

3. Offline repair then translate
   service.repair_nested("messy.svg", output="clean.svg")
   service.extract_and_inject("source.svg", "clean.svg", ...)
```

### Implementation sketch

```python
def analyze_nested(self, svg_path: Path | str) -> OperationResult[list[str]]:
    try:
        findings = self._nested.analyze(Path(svg_path))
        return OperationResult.ok(data=findings)
    except Exception as exc:
        return OperationResult.fail(str(exc), error_code=getattr(exc, "code", "nested_analyze_error"))

def repair_nested(
    self,
    svg_path: Path | str,
    *,
    output: Path | str | None = None,
    strategy: str | None = None,
    save: bool = True,
) -> OperationResult:
    try:
        tree = self._nested.repair(
            Path(svg_path),
            strategy=strategy or self.config.nested_strategy,
        )
        if save:
            if output is None:
                return OperationResult.fail("save=True but no output path", error_code="missing_output_path")
            self._save_tree(tree, Path(output))
        return OperationResult.ok(data=tree)
    except Exception as exc:
        return OperationResult.fail(str(exc), error_code=getattr(exc, "code", "nested_repair_error"))
```

Reuse the same `_save_tree` helper already present on the service.

### What **not** to do

- Do not call `MatchFixNestedTags` (or any file-based fixer) from inside `extract` / `inject`.
- Do not make repair the default when `nested_strategy="raise"`.
- Do not keep two competing repair paths (one in preparation via `NestedTspanFlattener`, another via the old fixer) without a clear ownership story.

---

## Summary of Recommended Actions

| Priority | Action |
|----------|--------|
| **High** | Rename/move `header_adder.py` → `titles/…` and merge its logic into `YearTitleHandler` |
| **High** | Make year-stripping pure (or clearly side-effecting with a return value) and respect `enable_year_titles` |
| **High** | Keep nested repair **out** of the default extract/inject path |
| **Medium** | Introduce `NestedStructureService` (or equivalent) and expose `analyze_nested` / `repair_nested` on `SVGTranslationService` |
| **Medium** | Thin-wrap or deprecate `MatchFixNestedTags`; make `NestedTspanFlattener` + `NestedTspanDetector` the real implementation |
| **Low** | Replace hard-coded `abr`/`ja` rules with a data-driven pattern list where possible |

---

## Target shape (after cleanup)

```text
titles/
  year_handler.py          # single owner of all year logic
  year_stripper.py         # (optional) extracted pure helpers

nested/
  detector.py
  flattener.py
  service.py               # NestedStructureService (analyze + repair)
  # fixer.py → deprecated thin wrapper or removed

service.py
  SVGTranslationService
    .extract / .inject / .extract_and_inject
    .analyze_nested        # new, opt-in
    .repair_nested         # new, opt-in
```

This keeps the main translation pipeline predictable, gives users an explicit way to diagnose and repair nested tags, and removes the misleading `header_adder` abstraction.
