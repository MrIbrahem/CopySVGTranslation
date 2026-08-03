**copy_svg_translation – Modern Class-Based Redesign**

### 1. Proposed Detailed File Structure + Class Names

```
copy_svg_translation/
├── __init__.py                 # Public API only
├── config.py
├── service.py                  # Main high-level facade
├── exceptions.py
├── result.py
│
├── core/
│   ├── __init__.py
│   ├── models.py               # Domain models - Shared small types / enums if needed
│   ├── text_node.py            # TextNode
│   ├── switch_node.py          # SwitchNode
│   └── mapping.py              # TranslationEntry + TranslationMapping
│
├── extraction/
│   ├── __init__.py
│   ├── extractor.py           # SVGTranslationExtractor
│   └── strategies.py          # Matching strategies (how default text links to translations)
│
├── injection/
│   ├── __init__.py
│   ├── preparer.py              # SvgPreparationPipeline
│   ├── injector.py              # SVGTranslationInjector (orchestrator only)
│   ├── id_manager.py            # IdManager
│   ├── switch_processor.py      # SwitchProcessor  ← replaces most of work_on_switches
│   ├── translation_applier.py   # TranslationApplier
│   └── steps/                   # Preparation only (runs before injection)
│       ├── base.py
│       ├── load.py
│       ├── validate.py
│       ├── normalize_tspans.py
│       ├── assign_ids.py
│       ├── split_languages.py
│       └── reorder.py
│
├── nested/
│   ├── __init__.py
│   ├── detector.py             # NestedTspanDetector
│   └── flattener.py            # NestedTspanFlattener - Prefer style-preserving version
│
├── titles/
│   ├── __init__.py
│   └── year_handler.py         # YearTitleHandler (single unified implementation)
│
├── io/
│   ├── __init__.py
│   ├── svg_document.py         # SvgDocument – load / save / root access
│   └── mapping_store.py        # MappingStore – load / merge / save JSON mappings
│
├── utils/
│   ├── __init__.py
│   ├── text.py                 # normalize_text, normalize_lang
│   └── xml.py                  # thin lxml / SVG helpers
│
└── legacy/                     # Temporary compatibility layer
    ├── __init__.py
    ├── extract.py
    ├── inject.py
    └── workflows.py
```

#### Key Classes (proposed)

| Module                     | Class                     | Responsibility                                                                   |
| -------------------------- | ------------------------- | -------------------------------------------------------------------------------- |
| `config.py`                | `TranslationConfig`       | All settings (case_insensitive, overwrite, pretty_print, auto_save, paths, etc.) |
| `result.py`                | `OperationResult[T]`      | Unified success/failure + data + stats + warnings                                |
| `result.py`                | `InjectorStats`           | Keep (slightly cleaned)                                                          |
| `core/models.py`           | `TranslationEntry`        | One source text → {lang: translation}                                            |
| `core/models.py`           | `TranslationMapping`      | Full mapping (`new`, `title`, `title_new`, …)                                    |
| `core/text_node.py`        | `TextNode`                | Wrapper around `<text>` / `<tspan>`                                              |
| `core/switch_node.py`      | `SwitchNode`              | Wrapper around `<switch>`                                                        |
| `extraction/extractor.py`  | `SVGTranslationExtractor` | Extract only                                                                     |
| `extraction/strategies.py` | `TspanIdMatchingStrategy` | How to match default ↔ translated tspans                                         |
| `injection/preparer.py`    | `SvgPreparationPipeline`  | Runs ordered steps                                                               |
| `injection/steps/base.py`  | `PreparationStep` (ABC)   | Base for each step                                                               |
| `injection/injector.py`    | `SVGTranslationInjector`  | Inject into prepared document                                                    |
| `injection/id_manager.py`  | `IdManager`               | Unique ID generation & tracking                                                  |
| `nested/flattener.py`      | `NestedTspanFlattener`    | Style-preserving preferred                                                       |
| `nested/detector.py`       | `NestedTspanDetector`     | Find problematic nodes                                                           |
| `titles/year_handler.py`   | `YearTitleHandler`        | Unify old + new title logic                                                      |
| `io/svg_document.py`       | `SvgDocument`             | Load / save / root access                                                        |
| `io/mapping_store.py`      | `MappingStore`            | Load / merge / save JSON mappings                                                |
| `service.py`               | `SVGTranslationService`   | **Main public facade**                                                           |

---

### 2. Phased Migration Plan

#### Phase 1 – Foundation & Compatibility (low risk, 1–2 weeks)

**Goal:** Introduce new structure without breaking existing callers.

1. Create `config.py`, `result.py`, `exceptions.py`, `core/models.py`.
2. Introduce `SVGTranslationService` that currently delegates to existing `extract` / `inject`.
3. Move current functions into `legacy/` and re-export them with `DeprecationWarning`.
4. Add `TranslationConfig` and start using it inside the service.
5. Unify error handling: convert internal `None` + `error` strings into `OperationResult`.
6. Keep public API backward-compatible:
    ```python
    from copy_svg_translation import extract, inject_file_tree, SVGTranslationService
    ```

**Exit criteria:** All existing tests pass; new service works as thin wrapper.

---

#### Phase 2 – Core Rewrite (medium risk, 2–4 weeks)

**Goal:** Move real logic into the new class-based design.

1. Implement `SvgDocument`, `IdManager`, `TextNode`, `SwitchNode`.
2. Rewrite `SVGTranslationExtractor` on top of the new models (keep old class temporarily).
3. Split preparation into pipeline steps (`PreparationStep` subclasses).
4. Implement new `SVGTranslationInjector` that uses the pipeline + `IdManager`.
5. Merge `titles.py` + `titles_new.py` → `YearTitleHandler`.
6. Promote `find_nested_new` logic into `NestedTspanFlattener` (style-preserving default).
7. Update `SVGTranslationService` to use the new classes instead of legacy functions.
8. Add comprehensive unit tests for models, pipeline steps, and service.

**Exit criteria:** New path is default; legacy path still works but marked deprecated.

---

#### Phase 3 – Cleanup & Modernization (low–medium risk, 1–2 weeks)

**Goal:** Remove technical debt and polish the API.

1. Delete or heavily reduce `legacy/` package.
2. Remove duplicate helpers and old title modules.
3. Make file I/O explicit only (no automatic `data/` or `translated/` folders unless configured).
4. Improve logging (structured, consistent levels).
5. Finalize public API in `__init__.py`:
    ```python
    from .service import SVGTranslationService
    from .config import TranslationConfig
    from .result import OperationResult, InjectorStats
    from .core.models import TranslationMapping
    ```
6. Optional: simple CLI that uses `SVGTranslationService`.
7. Documentation + migration guide for users of the old functions.

**Exit criteria:** Clean class-based API only; full test coverage on critical paths; no silent disk writes.

---

### Recommended Public API (after Phase 3)

```python
from pathlib import Path
from copy_svg_translation import SVGTranslationService, TranslationConfig

config = TranslationConfig(
    case_insensitive=True,
    overwrite=False,
    pretty_print=True,
    auto_save=False,
)

service = SVGTranslationService(config)

# Extract
result = service.extract(Path("source.svg"))
if result.success:
    mapping = result.data

# Inject
result = service.inject(Path("target.svg"), mapping, output=Path("out.svg"))

# Combined
result = service.extract_and_inject(
    source=Path("translated.svg"),
    target=Path("untranslated.svg"),
    output=Path("result.svg"),
)
```

---

**Suggested order of work**

1. Phase 1 (safe foundation)
2. Nested tspans + YearTitleHandler (high value, relatively isolated)
3. Preparation pipeline + Injector
4. Extractor rewrite
5. Phase 3 cleanup

---

**Full Design: `TranslationConfig` + `SVGTranslationService`**

### 1. `TranslationConfig`

```python
# config.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass(slots=True)
class TranslationConfig:
    """
    Central configuration for all SVG translation operations.
    Immutable by convention – create a new instance to change settings.
    """

    # --- Matching / lookup ---
    case_insensitive: bool = True
    """Treat source text keys as case-insensitive (lowercased)."""

    # --- Injection behaviour ---
    overwrite: bool = False
    """If True, update existing language nodes instead of skipping them."""

    pretty_print: bool | None = None
    """Pretty-print the output SVG when saving."""

    # --- Nested tspan handling ---
    nested_strategy: Literal["preserve_style", "flatten", "raise"] = "preserve_style"
    """
    How to handle nested <tspan> (and <a>) elements:
    - preserve_style: convert nested styled tspans into sibling tspans (preferred)
    - flatten: concatenate all text into a single tspan
    - raise: raise an error when nested tspans are found
    """

    # --- Title / year handling ---
    enable_year_titles: bool = True
    """Enable special handling for titles that contain a 4-digit year."""

    # --- I/O behaviour ---
    auto_save: bool = False
    """If True, save results automatically when an output path is available."""

    output_dir: Path | None = None
    """Default directory for output SVGs (used when only a filename is given)."""

    mapping_output_dir: Path | None = None
    """Default directory for extracted JSON mapping files."""

    create_parents: bool = True
    """Create parent directories when saving files."""

    # --- Parsing / preparation ---
    remove_blank_text: bool = True
    """Pass remove_blank_text=True to the XML parser."""

    normalize_languages: bool = True
    """Normalize systemLanguage values (e.g. en_us → en-US)."""

    assign_missing_ids: bool = True
    """Automatically assign trsvgN IDs to translatable nodes that lack an id."""

    # --- Logging / diagnostics ---
    collect_warnings: bool = True
    """Collect non-fatal warnings into OperationResult.warnings."""

    # --- Advanced / future ---
    extra: dict = field(default_factory=dict, repr=False)
    """Escape hatch for experimental or one-off options."""

    def with_updates(self, **kwargs) -> TranslationConfig:
        """Return a new config with the given fields replaced."""
        from dataclasses import replace
        return replace(self, **kwargs)
```

---

### 2. Supporting Result Types

```python
# result.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from lxml import etree

T = TypeVar("T")


@dataclass(slots=True)
class InjectorStats:
    all_languages: int = 0
    new_languages: int = 0
    processed_switches: int = 0
    inserted_translations: int = 0
    skipped_translations: int = 0
    updated_translations: int = 0
    languages_before: list[str] = field(default_factory=list)
    languages_after: list[str] = field(default_factory=list)
    error: str = ""

    def to_json(self) -> dict[str, Any]:
        """Serialize stats to a JSON-compatible dictionary."""
        return {
            "all_languages": self.all_languages,
            "new_languages": self.new_languages,
            "processed_switches": self.processed_switches,
            "inserted_translations": self.inserted_translations,
            "skipped_translations": self.skipped_translations,
            "updated_translations": self.updated_translations,
            "languages_before": self.languages_before,
            "languages_after": self.languages_after,
            "error": self.error,
        }


@dataclass(slots=True)
class OperationResult(Generic[T]):
    success: bool
    data: T | None = None
    stats: InjectorStats | None = None
    error: str | None = None
    error_code: str | None = None
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def ok(
        cls,
        data: T,
        stats: InjectorStats | None = None,
        warnings: list[str] | None = None,
    ) -> OperationResult[T]:
        return cls(
            success=True,
            data=data,
            stats=stats,
            warnings=warnings or [],
        )

    @classmethod
    def fail(
        cls,
        error: str,
        error_code: str | None = None,
        stats: InjectorStats | None = None,
        warnings: list[str] | None = None,
    ) -> OperationResult[T]:
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            stats=stats,
            warnings=warnings or [],
        )


# Convenience aliases
ExtractResult = OperationResult["TranslationMapping"]          # forward ref
InjectResult = OperationResult[etree._ElementTree]
```

---

### 3. `SVGTranslationService` (Full Design)

```python
# service.py
from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from lxml import etree

from .config import TranslationConfig
from .core.models import TranslationMapping
from .result import InjectResult, InjectorStats, OperationResult

logger = logging.getLogger(__name__)


class SVGTranslationService:
    """
    Main public facade for SVG translation extraction and injection.

    All high-level operations go through this class.
    Low-level components (extractor, injector, preparer, etc.) are
    created internally from the supplied TranslationConfig.
    """

    def __init__(self, config: TranslationConfig | None = None) -> None:
        self.config = config or TranslationConfig()
        self._extractor = None
        self._injector = None
        self._mapping_store = None
        # Lazy init of collaborators is recommended

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(
        self,
        svg_path: Path | str,
        *,
        save_mapping: bool | Path | None = None,
    ) -> OperationResult[TranslationMapping]:
        """
        Extract translations from an SVG file.

        Parameters
        ----------
        svg_path:
            Source SVG file.
        save_mapping:
            - None / False → do not save
            - True → save to config.mapping_output_dir / <name>.json
            - Path → save to the given path

        Returns
        -------
        OperationResult[TranslationMapping]
        """
        svg_path = Path(svg_path)

        try:
            mapping = self._get_extractor().extract(svg_path)
        except Exception as exc:
            logger.exception("Extraction failed for %s", svg_path)
            return OperationResult.fail(
                error=str(exc),
                error_code=getattr(exc, "code", "extraction_error"),
            )

        if not mapping or mapping.is_empty():
            return OperationResult.fail(
                error="No translations found or file could not be parsed",
                error_code="no_translations",
            )

        warnings: list[str] = []

        if save_mapping:
            try:
                out = self._resolve_mapping_output(svg_path, save_mapping)
                self._get_mapping_store().save(mapping, out)
            except (OSError, Exception) as exc:
                warnings.append(f"Failed to save mapping: {exc}")

        return OperationResult.ok(data=mapping, warnings=warnings)

    def inject(
        self,
        svg_path: Path | str,
        mapping: TranslationMapping | Mapping[str, Any],
        *,
        output: Path | str | None = None,
        save: bool | None = None,
    ) -> InjectResult:
        """
        Inject translations into an SVG file.

        Parameters
        ----------
        svg_path:
            Target SVG to inject into.
        mapping:
            TranslationMapping or a raw dict compatible with it.
        output:
            Destination path. Required when saving.
        save:
            Override config.auto_save. If None, uses config.auto_save.

        Returns
        -------
        OperationResult[etree._ElementTree]
        """
        svg_path = Path(svg_path)
        should_save = self.config.auto_save if save is None else save

        if should_save and output is None:
            return OperationResult.fail(
                error="save=True but no output path provided",
                error_code="missing_output_path",
            )

        try:
            normalized = TranslationMapping.from_any(mapping)
            resolved_output = self._resolve_output_path(output) if output else None
            tree, stats = self._get_injector().inject(
                svg_path,
                normalized,
                save_path=resolved_output,
                save=should_save,
            )
        except Exception as exc:
            logger.exception("Injection failed for %s", svg_path)
            return OperationResult.fail(
                error=str(exc),
                error_code=getattr(exc, "code", "injection_error"),
            )

        if tree is None:
            return OperationResult.fail(
                error="Injection returned no tree",
                error_code="injection_failed",
                stats=stats,
            )

        return OperationResult.ok(data=tree, stats=stats)

    def extract_and_inject(
        self,
        source: Path | str,
        target: Path | str,
        *,
        output: Path | str | None = None,
        save_mapping: bool | Path | None = None,
        save: bool | None = None,
    ) -> InjectResult:
        """
        Extract translations from `source` and inject them into `target`.

        This is the most common high-level workflow.
        """
        extract_result = self.extract(source, save_mapping=save_mapping)
        if not extract_result.success or extract_result.data is None:
            return OperationResult.fail(
                error=extract_result.error or "Extraction failed",
                error_code=extract_result.error_code,
                warnings=extract_result.warnings,
            )

        inject_result = self.inject(
            target,
            extract_result.data,
            output=output,
            save=save,
        )

        # Merge warnings from extract_result into inject_result
        merged_warnings = extract_result.warnings + inject_result.warnings
        return OperationResult(
            success=inject_result.success,
            data=inject_result.data,
            stats=inject_result.stats,
            error=inject_result.error,
            error_code=inject_result.error_code,
            warnings=merged_warnings,
        )

    def prepare_only(
        self,
        svg_path: Path | str,
        *,
        output: Path | str | None = None,
    ) -> InjectResult:
        """
        Run only the preparation pipeline (normalize structure, IDs,
        language splitting, etc.) without injecting any translations.
        Useful for cleaning SVGs before manual translation or other tools.
        """
        svg_path = Path(svg_path)

        try:
            tree = self._get_injector().prepare(svg_path)
            if output:
                resolved_output = self._resolve_output_path(output)
                self._save_tree(tree, resolved_output)
            return OperationResult.ok(data=tree)
        except Exception as exc:
            return OperationResult.fail(
                error=str(exc),
                error_code=getattr(exc, "code", "prepare_error"),
            )

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def load_mapping(self, path: Path | str) -> OperationResult[TranslationMapping]:
        """Load a previously saved JSON mapping file."""
        try:
            mapping = self._get_mapping_store().load(Path(path))
            return OperationResult.ok(data=mapping)
        except Exception as exc:
            return OperationResult.fail(error=str(exc), error_code="load_mapping_error")

    def save_mapping(
        self,
        mapping: TranslationMapping,
        path: Path | str,
    ) -> OperationResult[Path]:
        """Save a mapping to JSON."""
        path = Path(path)
        try:
            self._get_mapping_store().save(mapping, path)
            return OperationResult.ok(data=path)
        except Exception as exc:
            return OperationResult.fail(error=str(exc), error_code="save_mapping_error")

    # ------------------------------------------------------------------
    # Internal helpers (lazy collaborators)
    # ------------------------------------------------------------------

    def _get_extractor(self):
        if self._extractor is None:
            from .extraction.extractor import SVGTranslationExtractor
            self._extractor = SVGTranslationExtractor(self.config)
        return self._extractor

    def _get_injector(self):
        if self._injector is None:
            from .injection.injector import SVGTranslationInjector
            self._injector = SVGTranslationInjector(self.config)
        return self._injector

    def _get_mapping_store(self):
        if self._mapping_store is None:
            from .io.mapping_store import MappingStore
            self._mapping_store = MappingStore(self.config)
        return self._mapping_store

    def _resolve_output_path(self, output: Path | str) -> Path:
        """
        Resolve output path for SVG files, applying output_dir only when
        the given path is a bare filename (no directory component).
        """
        output = Path(output)
        if output.parent == Path(".") and self.config.output_dir is not None:
            return self.config.output_dir / output
        return output

    def _resolve_mapping_output(
        self,
        svg_path: Path,
        save_mapping: bool | Path,
    ) -> Path:
        if isinstance(save_mapping, (str, Path)):
            return Path(save_mapping)

        if self.config.mapping_output_dir is None:
            raise ValueError(
                "mapping_output_dir is not configured; cannot resolve mapping output path"
            )

        base_dir = self.config.mapping_output_dir
        if self.config.create_parents:
            base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / f"{svg_path.name}.json"

    def _save_tree(self, tree: etree._ElementTree, path: Path) -> None:
        if self.config.create_parents:
            path.parent.mkdir(parents=True, exist_ok=True)
        tree.write(
            str(path),
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=self.config.pretty_print,
        )
```

---

### 4. Typical Usage Examples

```python
from pathlib import Path
from copy_svg_translation import SVGTranslationService, TranslationConfig

# Default config
service = SVGTranslationService()

# Custom config
config = TranslationConfig(
    case_insensitive=True,
    overwrite=True,
    nested_strategy="preserve_style",
    auto_save=False,
    pretty_print=True,
)
service = SVGTranslationService(config)

# Extract only
result = service.extract("chart_en_ar.svg", save_mapping=True)
if result.success:
    mapping = result.data
    print(mapping.new.keys())

# Inject only
result = service.inject(
    "chart_blank.svg",
    mapping,
    output="chart_translated.svg",
    save=True,
)
if result.success:
    print(result.stats.inserted_translations)

# One-shot workflow
result = service.extract_and_inject(
    source="already_translated.svg",
    target="new_version.svg",
    output="new_version_translated.svg",
    save=True,
)
```

---

### 5. Design Notes

| Decision                                   | Rationale                                                                              |
| ------------------------------------------ | -------------------------------------------------------------------------------------- |
| Single `TranslationConfig`                 | Avoid long parameter lists; easy to extend and pass around                             |
| `OperationResult[T]`                       | Consistent success/failure handling; no more mixed `None` / exceptions / error strings |
| Lazy collaborators                         | Faster startup; easier testing (can inject mocks later)                                |
| `extract_and_inject` as first-class method | Covers the most common user workflow cleanly                                           |
| Explicit `save` / `output`                 | No surprise writes to `cwd/data` or `cwd/translated`                                   |
| `with_updates()` on config                 | Convenient immutable-style changes                                                     |
| `prepare_only`                             | Useful for cleaning SVGs without translation                                           |
