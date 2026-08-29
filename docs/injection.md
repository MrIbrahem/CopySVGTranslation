# Injection

Injection applies a `TranslationMapping` (or a compatible dict) to an SVG,
inserting or updating `<text systemLanguage="XX">` nodes inside each `<switch>`.
The high-level entry point is `SVGTranslationService.inject()`; the engine is
`SVGTranslationInjector`.

## The injection pipeline

`SVGTranslationInjector.inject()` performs, in order:

1. **Prepare** the target with `SvgPreparationPipeline.run()` — normalizes
   structure, IDs, language tags, and wraps loose text in `<switch>` elements.
   (See [preparation.md](preparation.md).)
2. **Snapshot** the languages present before injection (`stats.languages_before`).
3. **Seed** the `IdManager` with existing element IDs to avoid collisions.
4. **Process every `<switch>`** with `SwitchProcessor.process()`:
    - find the fallback `<text>`,
    - read its default text segments,
    - enrich the mapping with year-title expansions,
    - for each language in the mapping, decide _skip / update / insert_ and call
      `TranslationApplier`,
    - reorder the switch (fallback last) when `sort_switches=True`.
5. **Finalize** switches (`_finalize_switches`).
6. **Snapshot** languages after (`stats.languages_after`) and compute totals.
7. **Write** the file if `save=True` and an `output` path is given.

## Using the service

```python
from CopySVGTranslation import SVGTranslationService

service = SVGTranslationService()
mapping = {
    "hello": {"ar": "مرحبا", "fr": "Bonjour"},
}
result = service.inject("target.svg", mapping, output="out.svg", save=True)

if result.success:
    print(result.stats.inserted_translations)
    tree = result.data.tree
```

### Insert vs. update vs. skip

For each language present in the mapping:

-   **inserted** — no node for that language existed; a clone of the fallback
    `<text>` is created with the right `systemLanguage` and translations.
-   **updated** — a node existed _and_ `overwrite_translations=True`; its `<tspan>`
    contents are overwritten in place.
-   **skipped** — a node existed but `overwrite_translations=False`; left unchanged.

These counts are reported in `InjectorStats`.

### Saving rules

-   `save=True` (or `config.auto_save`) **requires** an `output` path, otherwise the
    method returns `OperationResult.fail(error_code="missing_output_path")`.
-   When `output` is a bare filename, `TranslationConfig.output_dir` is prepended
    (unless it is unset). A path with a directory component is used unchanged.

## Overwriting behavior

`TranslationConfig.overwrite_translations` controls whether existing language
nodes are replaced. Leave it `False` (default) to preserve hand-maintained
translations; set `True` to refresh them from the mapping.

## Fallback-to-default

With `TranslationConfig.fallback_to_default_text=True`, a language that has no
translation in the mapping falls back to the default source segment instead of
being skipped.

## Errors

`inject()` returns `OperationResult.fail(...)` (not an exception) when:

-   the file does not exist,
-   the mapping is empty,
-   preparation fails (`SvgNestedTspanError`, `SvgStructureError`, parse errors),
-   or the resulting tree is `None`.

Inspect `result.error_code` / `result.error`. For a fully failed run,
`result.stats` may still carry partial counts.
