# CopySVGTranslation — Codebase Audit Report

**Generated**: 2025-08-02
**Commit**: `9e055fd`
**Scope**: Full codebase (standard effort)
**Categories audited**: correctness/bugs, security, performance, test coverage, tech debt & architecture, dependencies & migrations, DX & tooling, docs, direction

---

## Repository Summary

| Dimension          | Value                                                       |
| ------------------ | ----------------------------------------------------------- |
| Language           | Python 3.10+                                                |
| Runtime dependency | `lxml>=4.9`                                                 |
| Build system       | Hatchling                                                   |
| Test framework     | pytest (391 tests, 382 `def test_` functions, 2 deselected) |
| CI                 | GitHub Actions — pytest on Ubuntu, Python 3.10 only         |
| Package            | PyPI via trusted publishing on GitHub release               |
| Source LOC         | ~1,976 lines across 19 `.py` modules                        |
| Test LOC           | ~63 test files across unit/integration/e2e                  |
| Lint/Format        | Ruff + Black + isort (configured, not in CI)                |
| Type checking      | mypy + pyright (configured, not in CI)                      |

### Architecture Overview

Two-phase pipeline: **Extraction** (parse SVG → collect translation pairs from `<switch>` elements) and **Injection** (prepare target SVG → insert `<text systemLanguage="XX">` nodes). A `workflows` module composes both phases. A `nested_analyze` module detects and fixes nested `<tspan>` structures. A `titles_workers` module handles year-suffixed title strings.

Public API: two primary classes (`SVGTranslationExtractor`, `SVGTranslationInjector`), two dataclasses (`ExtractorData`, `InjectorData`), two workflow functions (`svg_extract_and_inject`, `svg_extract_and_injects`), and two legacy wrappers (`extract`, `inject`).

---

## Findings Table

Ordered by leverage (impact ÷ effort, discounted by confidence and fix-risk).

| #   | Finding                                                                 | Category  | Impact | Effort | Risk | Confidence | Evidence                        |
| --- | ----------------------------------------------------------------------- | --------- | ------ | ------ | ---- | ---------- | ------------------------------- |
| 1   | **Injector accumulates state across calls**                             | Bug       | HIGH   | S      | LOW  | HIGH       | `svg_injector.py:38-39`         |
| 2   | **Extractor accumulates state across calls**                            | Bug       | HIGH   | S      | LOW  | HIGH       | `svg_extractor.py:43`           |
| 3   | **`_parse_svg` catches `(OSError, Exception)` too broadly**             | Bug       | MED    | S      | LOW  | HIGH       | `svg_injector.py:209`           |
| 4   | **`svg_extract_and_inject` not in `__all__` or top-level exports**      | Bug       | MED    | S      | LOW  | HIGH       | `__init__.py:1-15`              |
| 5   | **`SvgTranslationPreparer.prepare()` not idempotent**                   | Bug       | MED    | S      | MED  | HIGH       | `preparation.py:56,88,127`      |
| 6   | **`svg_extract_and_inject` has mandatory disk side effects**            | Tech debt | MED    | M      | LOW  | HIGH       | `workflows.py:40-41`            |
| 7   | **`find_nested.py` vs `find_nested_new.py` — parallel implementations** | Tech debt | MED    | M      | MED  | HIGH       | `nested_analyze/`               |
| 8   | **CI runs only on Python 3.10, no lint/typecheck**                      | DX        | MED    | S      | LOW  | HIGH       | `.github/workflows/pytest.yaml` |
| 9   | **Missing type annotations on key methods**                             | Tech debt | LOW    | M      | LOW  | HIGH       | `svg_extractor.py:50,73,124`    |
| 10  | **`fix_nested_file` overwrites input by default**                       | Bug       | LOW    | S      | MED  | HIGH       | `find_nested.py:86`             |

---

## Detailed Findings

### [BUG-01] Injector accumulates state across calls (HIGH impact)

-   **Evidence**: `CopySVGTranslation/injection/svg_injector.py:38-39` — `self.result` and `self.new_stats` are created once in `__init__`, then mutated on every call to `inject()`. `self.new_stats` is a reference to `self.result.new_stats`.
-   **Impact**: Calling `inject()` twice on the same `SVGTranslationInjector` instance produces incorrect statistics. The counters (inserted, processed, skipped, updated) accumulate across calls. The returned `InjectorData` is always the same object — callers who store the result from call 1 see it silently mutated when call 2 happens. Additionally, if call 1 fails (setting `error`), call 2 on a valid file still shows the stale error from call 1 because the error string is never reset.
-   **Reproduction**:
    ```python
    inj = SVGTranslationInjector()
    r1 = inj.inject(file_a, mappings)  # inserted=1
    r2 = inj.inject(file_b, mappings)  # inserted=2 (accumulated!)
    assert r1 is r2  # Same object — r1.new_stats.inserted_translations is now 2
    ```
-   **Error persistence reproduction**:
    ```python
    inj = SVGTranslationInjector()
    inj.inject('/nonexistent.svg', mappings)  # error = 'File does not exist'
    r = inj.inject(valid_file, mappings)      # error STILL = 'File does not exist'
    ```
-   **Effort**: S — reset `self.result` and `self.new_stats` at the start of `inject()`.
-   **Risk**: LOW — purely additive fix, no external API changes.
-   **Confidence**: HIGH — verified with runtime test.
-   **Fix sketch**: At the top of `inject()`, create fresh `InjectorData()` and `InjectorStats` instances instead of reusing `self.result`/`self.new_stats`.

---

### [BUG-02] Extractor accumulates state across calls (HIGH impact)

-   **Evidence**: `CopySVGTranslation/extraction/svg_extractor.py:43` — `self.translations = ExtractorData()` is set once in `__init__`. The `process_switches()` method calls `self.translations.new[store_key] = {}` and `self.translations.tspans_by_id.update(...)`, which accumulate across files.
-   **Impact**: If an `SVGTranslationExtractor` instance is reused for multiple files (e.g., in a batch processing loop), the second `extract()` call returns translations from BOTH files. This is a silent data corruption bug — the caller believes they're getting data for file B, but they're getting file A ∪ file B.
-   **Reproduction**:
    ```python
    ext = SVGTranslationExtractor(file_a)
    r1 = ext.extract()  # keys = ['hello']
    ext.source_file = file_b
    r2 = ext.extract()  # keys = ['hello', 'world'] — r1 is also mutated!
    ```
-   **Effort**: S — reset `self.translations` at the start of `extract()`.
-   **Risk**: LOW — purely additive fix.
-   **Confidence**: HIGH — verified with runtime test.
-   **Fix sketch**: At the top of `extract()`, set `self.translations = ExtractorData()`.

---

### [BUG-03] `_parse_svg` catches exceptions too broadly (MED impact)

-   **Evidence**:
    -   `CopySVGTranslation/injection/svg_injector.py:209` — `except (OSError, Exception) as exc:` catches everything including `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit`.
    -   `CopySVGTranslation/nested_analyze/find_nested.py:102` — bare `except Exception:` in `fix_nested_file`.
    -   `CopySVGTranslation/nested_analyze/find_nested_new.py:170` — same pattern.
    -   `CopySVGTranslation/injection/svg_injector.py:287` — `except Exception as e:` in file write block.
    -   `CopySVGTranslation/utils/injection_utils.py:74` — `except Exception as exc:` in `load_all_mappings`.
-   **Impact**: `KeyboardInterrupt` (Ctrl+C) and `SystemExit` are swallowed silently, making it hard to stop the program or propagate fatal errors. A memory error or recursion error would also be caught and stored as a string in `error`, hiding the real problem.
-   **Effort**: S — change to `except (OSError, ValueError) as exc:` or similar specific types; let `BaseException` subclasses propagate.
-   **Risk**: LOW — narrowing exception handlers doesn't change happy-path behavior.
-   **Confidence**: HIGH.
-   **Fix sketch**: Replace `(OSError, Exception)` with specific exception types. For XML parsing: `(etree.XMLSyntaxError, OSError)`. For file I/O: `(OSError, IOError)`.

---

### [BUG-04] `svg_extract_and_inject` and `svg_extract_and_injects` not exported (MED impact)

-   **Evidence**: `CopySVGTranslation/__init__.py:1-15` — the `__all__` list includes `extract`, `inject`, `ExtractorData`, `InjectorData`, `match_nested_tags`, `fix_nested_file`, but NOT `svg_extract_and_inject` or `svg_extract_and_injects`. These are documented in the README as part of the public API.
-   **Impact**: Users who do `from CopySVGTranslation import svg_extract_and_inject` get an `ImportError`. Users following the README's "Extracting and injecting in a single step" example cannot use the documented import path. The functions ARE accessible via `CopySVGTranslation.workflows.svg_extract_and_inject`, but that's an internal module path.
-   **Effort**: S — add the imports and `__all__` entries.
-   **Risk**: LOW — purely additive.
-   **Confidence**: HIGH — verified with runtime import test: `hasattr(CopySVGTranslation, 'svg_extract_and_inject')` returns `False`.
-   **Fix sketch**: Add to `__init__.py`:
    ```python
    from .workflows import svg_extract_and_inject, svg_extract_and_injects
    ```
    and add both to `__all__`.

---

### [BUG-05] `SvgTranslationPreparer.prepare()` not idempotent (MED impact)

-   **Evidence**: `CopySVGTranslation/injection/preparation.py:56,88,127` — `_collect_tspans_as_translatable()` appends to `self.translatable_nodes` without clearing it first. `_wrap_loose_text_into_tspans()` also appends. If `prepare()` is called twice on the same instance, `translatable_nodes` accumulates duplicate entries, though `_rebuild_translatable_nodes()` at line 133 partially mitigates this by replacing the list.
-   **Impact**: If a caller reuses a `SvgTranslationPreparer` instance (e.g., by calling `prepare()` again after modifying the file), the validation in `_collect_tspans_as_translatable()` may raise `SvgNestedTspanExceptionError` incorrectly because it processes stale nodes. The `_collect_existing_ids()` and `_clean_ids_and_remove_empty_nodes()` methods also don't fully reset their state. In practice, this is low-impact because `SvgTranslationPreparer` is typically created fresh for each call in `_parse_svg()`, but the class's public API implies it should be reusable.
-   **Effort**: S — add a `_reset()` method called at the top of `prepare()`.
-   **Risk**: MED — must ensure the reset doesn't break the partial-reuse patterns if any exist.
-   **Confidence**: HIGH — verified with runtime test showing `translatable_nodes` grows on second call.
-   **Fix sketch**: At the start of `prepare()`, reset: `self.existing_ids = set()`, `self.ids_in_use = [0]`, `self.translatable_nodes = []`.

---

### [TECH-01] `svg_extract_and_inject` has mandatory disk side effects (MED impact)

-   **Evidence**: `CopySVGTranslation/workflows.py:30-41` — the function always writes a JSON file and creates directories, even when `save_result=False`. Lines 30-34 create `data/` directory, lines 40-41 unconditionally `json.dump()` to it. Line 46-47 creates `translated/` directory.
-   **Impact**: Users cannot use this function as a pure in-memory pipeline. Every call writes to the filesystem, which is surprising for a function that accepts `save_result=False`. In serverless/ephemeral environments or when processing many files, this creates unwanted I/O and directory clutter. The function also uses `Path.cwd()` which makes behavior depend on the working directory.
-   **Effort**: M — make the JSON write conditional (add a parameter like `cache_json=True`), and make the `all_mappings_file` and `save_path` defaults lazy (only create when needed).
-   **Risk**: LOW — additive changes with backward-compatible defaults.
-   **Confidence**: HIGH.
-   **Fix sketch**: Add `cache_json: bool = True` parameter. When `cache_json=False`, pass the extracted mappings directly to `inject()` via `all_mappings=` instead of going through a JSON file on disk.

---

### [TECH-02] `find_nested.py` vs `find_nested_new.py` — unresolved duplication (MED impact)

-   **Evidence**: `CopySVGTranslation/nested_analyze/find_nested.py` (111 lines) and `CopySVGTranslation/nested_analyze/find_nested_new.py` (180 lines) contain parallel implementations of `match_nested_tags()`, `fix_nested_tspans()`, and `fix_nested_file()`. The `__init__.py` only exports from `find_nested.py`. The `find_nested_new.py` has a TODO block (lines 1-34) describing desired behavior and tests marked with `@pytest.mark.todo`.
-   **Impact**: Two implementations with the same function names but different behavior (the "new" version preserves styling by creating sibling tspans; the "old" version flattens all text into one tspan). Callers cannot easily discover or use the new implementation. The old version loses styling information when fixing nested tspans. The TODO has been unresolved through multiple commits.
-   **Effort**: M — decide which behavior is correct, consolidate into one module, update exports and tests.
-   **Risk**: MED — changing the flattening behavior could break downstream consumers that depend on the current output format.
-   **Confidence**: HIGH.
-   **Fix sketch**: Either (a) replace `find_nested.py` internals with `find_nested_new.py` behavior and update tests, or (b) rename to make the distinction clear (e.g., `flatten_nested` vs `split_nested`). Remove the TODO.

---

### [DX-01] CI runs only on Python 3.10, no lint/typecheck (MED impact)

-   **Evidence**: `.github/workflows/pytest.yaml` — `python-version: "3.10"` only. No ruff, mypy, or pyright step. The project claims `requires-python = ">=3.10"` and configures mypy for `python_version = "3.13"` and pyright for `pythonVersion = "3.13"`, but CI never runs them.
-   **Impact**: Regressions on Python 3.11/3.12/3.13 go undetected. Type errors accumulate silently. Ruff violations (the project has extensive ruff config) are never caught in CI. A contributor can push code that fails `ruff check` or `mypy` and CI passes.
-   **Effort**: S — add a Python version matrix and a lint job to the existing workflow.
-   **Risk**: LOW — additive CI changes, no source code impact.
-   **Confidence**: HIGH.
-   **Fix sketch**: Add `strategy.matrix.python-version: ["3.10", "3.11", "3.12", "3.13"]` and a separate lint job running `ruff check` and `mypy`.

---

### [TECH-03] Missing type annotations on key public methods (LOW impact)

-   **Evidence**:
    -   `svg_extractor.py:50` — `get_english_default_texts(self, text_elements)` — no type on `text_elements` parameter or return type.
    -   `svg_extractor.py:73` — `process_switch_translations(self, text_elements, ...)` — same issue.
    -   `svg_extractor.py:124` — `process_switches(self, root: etree.Element)` — return type missing.
    -   `svg_injector.py:60` — `work_on_switches(self, root, mappings, existing_ids)` — `root` and `mappings` lack types.
    -   `elements_utils.py:65` — `sort_switch_texts(elem)` — no type annotation.
-   **Impact**: Type checkers cannot verify correctness at module boundaries. Users of the public API get poor IDE completions. mypy in `disallow_untyped_defs = false` mode masks this, but anyone using strict mode downstream gets unhelpful `Any` types.
-   **Effort**: M — ~15 methods across 3 files need annotations.
-   **Risk**: LOW — purely additive, no behavior change.
-   **Confidence**: HIGH.
-   **Fix sketch**: Add type annotations following the patterns already used in `preparation.py` (which is well-annotated). Use `list[etree._Element]` for element lists, `Mapping[str, Any]` for mappings, etc.

---

### [BUG-06] `fix_nested_file` overwrites input file by default (LOW impact)

-   **Evidence**: `CopySVGTranslation/nested_analyze/find_nested.py:86` and `find_nested_new.py:151` — `new_path = Path(new_path or source_file)` means when `new_path` is `None` (the default), the function overwrites the input file in place.
-   **Impact**: Destructive operation by default. A caller who forgets to pass `new_path` silently loses the original file. This is especially dangerous because the function flattens nested tspans, which is a lossy transformation (styling information is discarded in the old implementation).
-   **Effort**: S — make `new_path` required, or raise when it's not provided.
-   **Risk**: MED — existing callers may depend on the overwrite behavior. Add a deprecation warning first.
-   **Confidence**: HIGH.
-   **Fix sketch**: Change signature to `fix_nested_file(source_file: Path, new_path: Path, ...)` making `new_path` required. Or add a `overwrite_input: bool = False` parameter.

---

## Audit Gaps — What Was NOT Audited

-   **`_works_files/`** — excluded (utility scripts, gitignored, not part of the package).
-   **`tests/manually/`** — manual test scripts, not part of the automated suite.
-   **Dependency audit** (`pip-audit`) — not run; the only runtime dependency is `lxml`, which is well-maintained.
-   **Performance profiling** — not applicable at this scale; the library processes individual SVG files.
-   **Security** — no network I/O, no user-facing endpoints, no credential handling. The library processes local files only. No security findings.

---

## Direction — Forward-Looking Suggestions

These are grounded options for the maintainer to weigh, not bugs to fix.

### 1. Batch processing API

The current API is file-at-a-time. The state accumulation bugs (BUG-01, BUG-02) suggest users may want to process multiple files, but there's no supported way to do it. A `SVGTranslationExtractor.extract_many(paths)` and `SVGTranslationInjector.inject_many(files, mappings)` would be a natural extension. **Evidence**: the extractor and injector both accept `Path` inputs and the workflow functions compose them — a batch API is one layer above. **Trade-off**: adds API surface; may not be needed if most users process one file at a time. **Effort**: M.

### 2. Consolidate `find_nested_new.py` into the main path

The "new" nested tspan fixer preserves styling by creating sibling tspans instead of flattening — this is clearly the better behavior. The TODO in `find_nested_new.py` describes the exact desired output. Once consolidated, the old flattening behavior should be deprecated. **Evidence**: the TODO block (lines 1-34 of `find_nested_new.py`) and the existence of tests marked `@todo` for this functionality. **Trade-off**: breaking change for callers who depend on the flat output. **Effort**: M.

### 3. Pure in-memory workflow

The `svg_extract_and_inject` function always touches the filesystem. An in-memory variant that accepts `str | bytes` SVG content and returns `str | bytes` would enable use in web services, notebooks, and pipelines where disk I/O is undesirable. **Evidence**: TECH-01 and the function's mandatory `mkdir`/`json.dump` calls. **Effort**: S-M.

### 4. Structured logging / progress reporting

The library uses `logging` throughout but has no structured progress mechanism. For large SVG files with hundreds of switches, callers have no way to track progress. A simple callback or iterator-based API would improve observability. **Evidence**: 30+ `logger.debug()` calls in the injector alone. **Effort**: M. **Trade-off**: adds complexity for a feature most users may not need.

---

## Findings Considered and Rejected

-   **"Use `Union` syntax consistently"** — The codebase uses both `X | Y` and `Optional[X]` styles. Not worth flagging; pyproject.toml explicitly disables `UP007` and `UP045` ruff rules. This is a decided style choice.
-   **"`__all__` on every submodule"** — All submodules already have `__all__` defined. No issue here.
-   **"Remove legacy `extract()`/`inject()` wrappers"** — The CLAUDE.md says "deprecated" but no removal timeline is stated. Not a finding; this is a tracked deprecation.
-   **"`.gitignore` includes `*.svg`"** — This is intentional (test SVG fixtures are explicitly un-ignored with `!tests/**/**.svg`). Not a finding.

---

## Recommended Execution Order

If implementing fixes:

1. **BUG-01** (injector state) — highest leverage, S effort, no dependencies
2. **BUG-02** (extractor state) — same pattern as BUG-01, S effort
3. **BUG-04** (missing exports) — S effort, no risk, immediate user benefit
4. **BUG-03** (broad exception catching) — S effort, defensive
5. **BUG-05** (preparer idempotency) — S effort
6. **DX-01** (CI matrix + lint) — S effort, prevents future regressions
7. **BUG-06** (fix_nested_file overwrite) — S effort, but needs deprecation path
8. **TECH-01** (mandatory disk I/O) — M effort
9. **TECH-02** (find_nested consolidation) — M effort, needs design decision
10. **TECH-03** (type annotations) — M effort, can be done incrementally

Plans 1-6 are independent and can be executed in any order. Plans 8-9 benefit from plans 1-6 being done first (cleaner state management).
