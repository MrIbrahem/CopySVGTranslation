# `SVGTranslationService` `target` / `output` Duplication Review

**Status:** Analysis only. This branch contains no production-code, test, or README changes.

**Scope:** This review focuses on `SVGTranslationService.extract_and_inject()`, specifically the following documentation example from the earlier documentation branch:

```python
service.extract_and_inject(
    source="source.svg",
    target="target.svg",
    output="target-translated.svg",
    save=True,
)
```

## Executive Summary

`target` and `output` do not currently mean the same thing. `target` is the **input SVG** into which translations are injected in memory, while `output` is the optional **destination file** for the resulting SVG. The existing API therefore supports a non-destructive workflow: it reads `target.svg` and writes a separate output file.

However, if the product decision is that `extract_and_inject()` must accept **one target file only**, retaining both parameters creates unnecessary cognitive overhead and makes the example confusing. The only coherent one-path design is to keep `target` as the file that is read and then updated **in place** when saving, and to remove `output` from this method only.

> `output` cannot replace `target` while leaving only one path parameter. The method still needs a path from which to read the target SVG. Therefore, the single remaining path must be `target`, not `output`.

| Recommended decision | Result |
| --- | --- |
| Remove `output` from `extract_and_inject()` | `target` becomes the only target-SVG path. |
| When `save=True` or `config.auto_save=True` | Write the result back to `target`. |
| When `save=False` | Return the modified tree in `OperationResult.data` without writing a file. |
| Future implementation scope | Do not change the `inject()`, `prepare_only()`, or `repair_nested()` contracts as part of this work. |

## Current Behavior and the Source of the Duplication

`extract_and_inject()` currently has three logical file paths: `source` for extracting translations, `target` for reading, preparing, and injecting into the target SVG, and `output` for writing the result when saving is enabled. The implementation follows this flow:

```text
source ──extract──> TranslationMapping
                         │
                         ▼
target ──inject(mapping, output, save)──> modified SVG in memory / saved file
```

In implementation terms, the method invokes `self.inject(target, extract_result.data, output=output, save=save)`. Consequently, `target` is not written automatically; saving depends on `output` whenever the effective `save` value is true.

| Parameter | Current meaning in `extract_and_inject()` | Required when saving? |
| --- | --- | --- |
| `source` | SVG that contains the translations to extract. | Yes; it is the extraction input. |
| `target` | SVG whose default-language text is matched and into which translations are injected in memory. | Yes; it is the injection input. |
| `output` | Separate path to which the injected SVG is written. | Yes, but only when the effective `save` value is true. |

This separation is technically valid when preserving the original `target` file is a requirement. It does not fit a one-target-file API, however: callers must name both the target and the transformed copy even when the intended operation is to update that target itself.

## Locations Where the Duplication Exists or Is Relied Upon

The following table distinguishes locations that would change in a future implementation from locations that use `output` for a different, valid purpose and should remain out of scope.

| Location | Evidence | Current role | Future action |
| --- | --- | --- | --- |
| [`CopySVGTranslation/service.py`, lines 211–248](../CopySVGTranslation/service.py#L211-L248) | `extract_and_inject(source, target, *, output=None, ...)` passes `output` to `inject()`. | Primary duplication point. | Remove `output` from the signature and direct saving to `target` when enabled. |
| [`CopySVGTranslation/service.py`, lines 151–209](../CopySVGTranslation/service.py#L151-L209) | `inject(svg_path, mapping, *, output=None, save=None)`. | Separates injection input from a destination copy. | **No change**. This lower-level API has a valid non-destructive use case. |
| [`CopySVGTranslation/service.py`, lines 305–313](../CopySVGTranslation/service.py#L305-L313) | `_resolve_output_path(output)`. | Applies `output_dir` to bare output filenames. | Retain for `inject()` and `prepare_only()`; do not use it in the combined workflow after `output` is removed. |
| [`tests/unit/test_service.py`, lines 100–120](../tests/unit/test_service.py#L100-L120) | `extract_and_inject(src, tgt)` test without saving. | Validates in-memory injection only; does not cover a save contract. | Update the test and add in-place `target` save coverage. |
| [`README.md`, lines 74–79](../README.md#L74-L79) | Current `main` example passes both `target` and `output`. | User-facing source of the confusion. | Replace with a one-`target` example after the API changes. |
| [PR #78 — documentation branch](https://github.com/MrIbrahem/CopySVGTranslation/pull/78) | The expanded examples repeat the separation, including `target="target.svg"` and `output="target-translated.svg"`. | Documentation not merged into `main` at the time of this review; it will be affected by the decision. | Update or rebase it on the new API before merging. |
| [`CopySVGTranslation/nested/service.py`, lines 79–125](../CopySVGTranslation/nested/service.py#L79-L125) | `repair_file(source, output, ...)`. | General file transformation that may write to a separate output or the source itself. | **Out of scope**. It is not part of the translation-copy workflow. |

## Detailed Proposal

### Public API After the Change

```python
result = service.extract_and_inject(
    source="source.svg",
    target="target.svg",
    save=True,
)
```

`source` retains its existing meaning. `target` becomes the only SVG path to which translations are applied and, when saving is enabled, the path to which the result is written. `output` is no longer part of the public API for this combined workflow.

The proposed signature is:

```python
def extract_and_inject(
    self,
    source: Path | str,
    target: Path | str,
    *,
    save_mapping: bool | Path | None = None,
    save: bool | None = None,
) -> OperationResult:
    ...
```

### Proposed Save Semantics

`extract_and_inject()` should calculate its effective save value in the same way as `inject()` currently does:

```python
should_save = self.config.auto_save if save is None else save
```

When `should_save` is true, the method should internally pass `target` as the save path. The expected behavior is:

| `save` | `config.auto_save` | Result |
| --- | --- | --- |
| `True` | Any value | Save over `target`. |
| `False` | Any value | Do not write a file; return the tree and statistics only. |
| `None` | `True` | Save over `target`. |
| `None` | `False` | Do not write a file; preserve the current in-memory default. |

### Protecting Against Data Loss

Removing `output` makes saving destructive for the target file. A future implementation should therefore use atomic writing: write to a temporary file in the same directory, then replace `target` only after the write succeeds. This does not preserve a logical backup of the original, but it prevents a partial write or an interrupted save from corrupting the target file.

If retaining an original copy is a real product requirement, it conflicts with the requirement of one target-file path. The product decision must then be explicit: either adopt the in-place update model proposed here or retain `output` as a non-destructive transformation model.

## Rejected Alternatives

| Alternative | Reason for rejection |
| --- | --- |
| Keep both `target` and `output`, but rename them to `input_target` and `destination`. | Improves naming only; it does not satisfy the one-target-path requirement. |
| Remove `target` and keep `output`. | Functionally impossible; there would be no path from which to read the SVG that receives the translations. |
| Change `inject()`, `prepare_only()`, and `repair_nested()` at the same time. | Unnecessary scope expansion that would break valid non-destructive transformation workflows outside the combined method. |
| Always save over `target`, regardless of `save`. | Breaks the current ability to preview the modified tree in memory. |

## Compatibility and Release Impact

This is a breaking change for callers of `extract_and_inject()` that pass `output=`. The change should therefore be released in a new major version. If a gradual transition is required, the method could temporarily accept `output` with a deprecation warning before removing it in the next major release. That transitional approach does not satisfy the one-parameter requirement immediately, so it is appropriate only if compatibility is more important than immediate API simplification.

## Recommended Future Implementation Plan

This plan is not implemented in this branch. It is the proposed follow-up work once the design decision is approved.

1. Remove `output` from the `SVGTranslationService.extract_and_inject()` signature and docstring.
2. Calculate `should_save` internally and pass `target` as the internal save path when required.
3. Add atomic target-file writing, or clearly document the risk if that safety measure is deferred.
4. Update the combined-workflow test to verify that `target` contains the injected language after `save=True`.
5. Add tests for `save=False`, plus `save=None` with both values of `auto_save`, and for write failures that must not corrupt the target.
6. Remove `output` from the README example and API table, and update [PR #78](https://github.com/MrIbrahem/CopySVGTranslation/pull/78) to match the new contract before merging it.
7. Publish migration notes stating that callers needing a non-destructive save still have `inject(svg_path, mapping, output=...)` available directly; the simplified `extract_and_inject()` flow would no longer offer that option.

## Review References

1. [`SVGTranslationService` in `service.py`](../CopySVGTranslation/service.py) — method signature, call flow, and save semantics.
2. [`SVGTranslationInjector` in `injection/injector.py`](../CopySVGTranslation/injection/injector.py) — internal `save_path` contract and save behavior.
3. [`Service tests`](../tests/unit/test_service.py) — current combined-workflow and save coverage.
4. [`README.md`](../README.md) and [PR #78](https://github.com/MrIbrahem/CopySVGTranslation/pull/78) — public examples and the locations of the confusion.
