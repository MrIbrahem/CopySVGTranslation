# Persistence and Output-Path Duplication Review

**Status:** Analysis only. This branch contains no production-code, test, or README changes.

**Scope:** This report reviews duplicated or inconsistent persistence, output-path, and save-control logic around `SVGTranslationService` and its collaborators. It retains the existing `extract_and_inject()` finding for context, but the primary focus of this revision is the **other duplication outside that method**.

## Executive Summary

The earlier review identified that `extract_and_inject()` exposes both `target` and `output`. That remains a valid API-design issue, but it is not the only duplication in the codebase. The review found four additional areas where output behavior is duplicated or materially inconsistent:

| Priority | Finding                                                                                                                        | Why it matters                                                                                                 |
| -------- | ------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| High     | The same SVG-writing behavior is implemented independently in the service, injector, and nested-structure service.             | The implementations already produce different output behavior, so fixes and guarantees can drift.              |
| High     | JSON mapping default-path logic exists in both `SVGTranslationService` and `MappingStore`, with conflicting fallback behavior. | A public helper is unused, and `save_mapping=True` can warn instead of using the documented conventional path. |
| Medium   | `inject()`, `prepare_only()`, and `repair_nested()` use three different save/output contracts.                                 | Callers cannot reliably transfer knowledge from one service method to another.                                 |
| Medium   | Deprecated injection wrappers duplicate the modern save contract but alter its semantics.                                      | Legacy callers can save merely by supplying a path, while modern callers must explicitly enable saving.        |

> The recommended direction is not to eliminate every `output` parameter. The real issue is duplicated responsibility for resolving paths and writing files. The implementation should centralize those responsibilities and define one consistent save contract for comparable service operations.

## Current Persistence Architecture

The package has four paths that can write artifacts: translated SVG injection, prepared SVG output, nested-structure repair, and JSON mapping persistence. Each path resolves destinations and writes files in a different location.

```text
SVGTranslationService
├── inject() ────────────────> SVGTranslationInjector._save()
├── prepare_only() ──────────> SVGTranslationService._save_tree()
├── repair_nested() ─────────> NestedStructureService._save_file()
└── extract()/save_mapping() ─> MappingStore.save()
```

This split is not inherently incorrect. The duplication becomes a maintenance problem because the methods serve the same general responsibility—persisting a transformed SVG or a derived mapping—while disagreeing on directory creation, formatting, XML declaration handling, default paths, and the meaning of a supplied path.

## Finding 1 — Duplicated SVG Writers With Divergent Behavior

### Evidence

Three separate private methods write transformed SVG content to disk.

| Writer                                | Location                                                                                        | Input            | Parent directories                                    | XML declaration       | Formatting source                                                             |
| ------------------------------------- | ----------------------------------------------------------------------------------------------- | ---------------- | ----------------------------------------------------- | --------------------- | ----------------------------------------------------------------------------- |
| `SVGTranslationService._save_tree()`  | [`service.py`, lines 331–341](../CopySVGTranslation/service.py#L331-L341)                       | `ElementTree`    | Creates parents when `config.create_parents` is true. | Always writes one.    | `config.pretty_print`, defaulting to `True`.                                  |
| `SVGTranslationInjector._save()`      | [`injection/injector.py`, lines 183–198](../CopySVGTranslation/injection/injector.py#L183-L198) | `ElementTree`    | Creates parents when `config.create_parents` is true. | Always writes one.    | `config.pretty_print`, defaulting to `True`.                                  |
| `NestedStructureService._save_file()` | [`nested/service.py`, lines 173–188](../CopySVGTranslation/nested/service.py#L173-L188)         | XML root element | Does **not** create parents.                          | Does not request one. | `etree.tostring(..., pretty_print=None)`, independent of `TranslationConfig`. |

The service and injector implementations are near-duplicates: both create parents conditionally, derive the same formatting default, and call `ElementTree.write()` with the same encoding and XML-declaration options. The nested writer performs the same broad job differently: it serializes a root element to Unicode text, writes it directly, does not create directories, and does not use the shared configuration.

### Impact

The output of `inject()`, `prepare_only()`, and `repair_nested()` is not governed by a single file-writing policy. For example, a new nested-repair output directory can fail even when `create_parents=True`, whereas the equivalent injection or preparation operation creates it. An SVG repaired through the nested service can also differ in declaration and formatting from an SVG written through the other two routes.

### Recommendation

Introduce one internal SVG writer, for example `SvgFileStore` or `write_svg_tree()`, under the I/O layer. It should accept an `ElementTree` or root element and consistently apply:

-   destination validation;
-   parent-directory creation based on `TranslationConfig.create_parents`;
-   UTF-8 encoding;
-   XML-declaration behavior;
-   `TranslationConfig.pretty_print`; and
-   atomic file replacement when an existing source may be overwritten.

Both `SVGTranslationService._save_tree()` and `SVGTranslationInjector._save()` should be removed in favor of that writer. `NestedStructureService._save_file()` should use it after wrapping its root in an `ElementTree`.

## Finding 2 — Duplicated Mapping Default-Path Resolution With Conflicting Semantics

### Evidence

Two components calculate a default location for an extracted JSON mapping.

| Location                                                                                                       | Behavior                                                                                                                                                    |
| -------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`SVGTranslationService._resolve_mapping_output()`, lines 315–329](../CopySVGTranslation/service.py#L315-L329) | When `save_mapping=True`, requires `config.mapping_output_dir`. If the option is `None`, it raises `ValueError`, which `extract()` converts into a warning. |
| [`MappingStore.default_mapping_path()`, lines 81–84](../CopySVGTranslation/io/mapping_store.py#L81-L84)        | Uses `config.mapping_output_dir` when configured; otherwise falls back to `<svg parent>/data/<svg name>.json`.                                              |

`MappingStore.default_mapping_path()` is not referenced elsewhere in the package. It is therefore a duplicate, inactive definition of the conventional path. More importantly, it does not agree with the active service behavior: one path has a `data/` fallback, while the other treats the absence of `mapping_output_dir` as a warning condition.

### Impact

A caller using `service.extract("source.svg", save_mapping=True)` receives a successful extraction with a warning unless `mapping_output_dir` is configured. The existence of an unused helper that advertises a usable fallback makes this behavior harder to understand and maintain. Future changes can update one rule but forget the other.

### Recommendation

Make `MappingStore.default_mapping_path()` the single authority for conventional mapping destinations. `SVGTranslationService._resolve_mapping_output()` should delegate to it for the `True` case, while retaining an explicit `Path` argument unchanged. The project must decide whether `<svg parent>/data/` is the desired default; if it is not, remove the unused helper instead of keeping two definitions.

## Finding 3 — Inconsistent Save and Output Contracts Across Service Methods

### Evidence

Comparable public operations use different combinations of output path and save flag.

| Public method                                                                              | Relevant signature                                                  | Save rule                                                                                | Output-path behavior                                                                   |
| ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| [`inject()`](../CopySVGTranslation/service.py#L151-L209)                                   | `inject(svg_path, mapping, *, output=None, save=None)`              | `save=None` uses `config.auto_save`; an effective true value requires `output`.          | Bare filenames are resolved through `config.output_dir`.                               |
| [`prepare_only()`](../CopySVGTranslation/service.py#L251-L274)                             | `prepare_only(svg_path, *, output=None)`                            | No `save` argument; supplying `output` always writes the file.                           | Bare filenames are resolved through `config.output_dir`.                               |
| [`repair_nested()`](../CopySVGTranslation/service.py#L61-L95)                              | `repair_nested(svg_path, *, output=None, strategy=None, save=True)` | Defaults to saving; an effective true value requires `output`.                           | The path is passed directly to the nested service; `config.output_dir` is not applied. |
| [`NestedStructureService.repair_file()`](../CopySVGTranslation/nested/service.py#L79-L125) | `repair_file(source, output=None, strategy=None, save=True)`        | Defaults to saving; when no output is supplied, its internal default is the source path. | Uses the supplied path directly and does not create parent directories.                |

The facade and its collaborator additionally disagree about `repair_file(output=None)`: the nested service can default to overwriting `source`, but `SVGTranslationService.repair_nested()` rejects that same call before delegation whenever `save=True`. This makes the lower-level fallback unreachable through the recommended facade.

### Impact

The same expression—supplying or omitting `output`—means different things depending on the operation. `prepare_only()` treats it as an implicit save instruction; `inject()` treats it as insufficient unless saving is also enabled; `repair_nested()` requires it by default; and the lower-level repair function uses a missing path as an in-place overwrite default. The caller must memorize method-specific rules rather than using a consistent model.

### Recommendation

Adopt a documented, uniform save contract for all high-level service methods that persist SVGs. A minimal and explicit model is:

| Case                                             | Recommended behavior                                                                                               |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| `output is None` and effective save is false     | Return the transformed tree only.                                                                                  |
| `output is None` and effective save is true      | Either fail uniformly or overwrite the input uniformly; choose one policy and apply it to every comparable method. |
| `output is provided` and effective save is false | Do not write; retain the path only if future API design needs it, otherwise reject this ambiguous combination.     |
| `output is provided` and effective save is true  | Resolve it through one path resolver and write using the shared SVG writer.                                        |

For backward compatibility, `prepare_only()` can initially preserve its path-implies-save behavior, but it should be documented as an exception or migrated to the shared rule in a major release. The facade must also choose whether nested repair supports in-place saves; the inner and outer methods should no longer disagree.

## Finding 4 — Legacy Adapters Duplicate and Change Modern Save Semantics

### Evidence

The deprecated injection API retains its own `save_path` and `save_result` contract.

| Location                                                                            | Behavior                                                                                              |
| ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| [`legacy/inject.py`, lines 19–84](../CopySVGTranslation/legacy/inject.py#L19-L84)   | `_inject_file_tree()` maps `save_path` to modern `output` and `save_result` to modern `save`.         |
| [`legacy/inject.py`, lines 87–118](../CopySVGTranslation/legacy/inject.py#L87-L118) | `inject_file_tree()` changes the supplied flag to `save_result or bool(save_path)` before delegation. |
| [`SVGTranslationService.inject()`](../CopySVGTranslation/service.py#L151-L209)      | Requires an effective true `save` value and an output path to write a file.                           |

The wrapper means that a legacy caller who supplies `save_path` but explicitly sets `save_result=False` still saves the file. A modern caller who supplies `output` and explicitly sets `save=False` does not. This behavior may be intentional as legacy compatibility, but it is a duplicate save-policy decision outside the modern service and is not evident from the service-level contract.

### Impact

The same concepts have four names and two rules across the codebase: `output`, `save`, `save_path`, and `save_result`. This increases documentation burden and makes migration from the legacy functions non-mechanical.

### Recommendation

Keep the wrappers only for compatibility, but make the divergence explicit in their deprecation documentation and tests. At the next major version, remove the wrappers rather than adding new save behavior to them. Do not make the modern service emulate `save_result or bool(save_path)`; that would further blur the modern contract.

## Existing `extract_and_inject()` Finding (Context Only)

The original finding remains valid: [`SVGTranslationService.extract_and_inject()`](../CopySVGTranslation/service.py#L211-L248) accepts both `target` (the SVG read and modified in memory) and `output` (a distinct saved copy). If the product requires a one-target-file combined workflow, keep `target`, remove `output` from that method, and save over `target` when the effective save value is true.

This finding is deliberately not the primary subject of the present revision. It should be implemented only after the shared writer and shared save contract have been decided; otherwise it risks adding another special case to an already inconsistent persistence layer.

## Recommended Implementation Sequence

No implementation is included in this branch. The following order reduces duplication without forcing an immediate breaking API change.

1. Decide the canonical high-level save contract, including whether in-place writes are allowed when no output path is supplied.
2. Add a shared SVG writer and migrate `inject()`, `prepare_only()`, and nested repair to it, preserving behavior through tests where intentionally required.
3. Add a shared output-path resolver and apply `output_dir` consistently, or document which operations intentionally bypass it.
4. Select one mapping default-path rule; delegate from the service to `MappingStore.default_mapping_path()` or remove that inactive helper.
5. Add tests that verify parity across writers: parent creation, encoding, declaration, pretty printing, and failures.
6. Add contract tests for every high-level save combination, including `save=None`, `auto_save`, missing output paths, bare filenames, and in-place repair decisions.
7. Update legacy migration guidance to state the `save_path`/`save_result` compatibility behavior precisely.
8. Only then implement the optional one-`target` simplification for `extract_and_inject()` and update the README examples.

## Suggested Test Matrix

| Scenario                                            | `inject()`                        | `prepare_only()`                  | `repair_nested()`                            | Expected common result after standardization       |
| --------------------------------------------------- | --------------------------------- | --------------------------------- | -------------------------------------------- | -------------------------------------------------- |
| Bare output filename with `output_dir`              | Covered by resolver helper tests. | Covered by resolver helper tests. | Not currently resolved through `output_dir`. | Same resolved path for all relevant methods.       |
| Missing parent directory with `create_parents=True` | Created.                          | Created.                          | Not created.                                 | Created for all persisted SVG output.              |
| Pretty-printed XML and declaration                  | Controlled by config.             | Controlled by config.             | Independent of config.                       | Controlled by config for all persisted SVG output. |
| Save disabled                                       | Returns modified tree.            | No explicit flag.                 | Defaults to save.                            | One documented and testable rule.                  |
| Missing output with save enabled                    | Fails.                            | Not applicable.                   | Facade fails; lower layer overwrites source. | One documented policy, applied consistently.       |

## Review References

1. [`SVGTranslationService` in `service.py`](../CopySVGTranslation/service.py) — public save contracts, output resolution, mapping output resolution, and the combined workflow.
2. [`SVGTranslationInjector` in `injection/injector.py`](../CopySVGTranslation/injection/injector.py) — injection-specific SVG writing behavior.
3. [`NestedStructureService` in `nested/service.py`](../CopySVGTranslation/nested/service.py) — repair path defaults and independent writing behavior.
4. [`MappingStore` in `io/mapping_store.py`](../CopySVGTranslation/io/mapping_store.py) — mapping persistence and unused default-path helper.
5. [`Legacy injection adapter`](../CopySVGTranslation/legacy/inject.py) — compatibility save-path and save-result behavior.
6. [`Service tests`](../tests/unit/test_service.py) and [`nested-service tests`](../tests/unit/nested/test_service_and_api.py) — current coverage of save operations and repair output.
