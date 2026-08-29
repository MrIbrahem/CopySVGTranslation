# Preparation

Before translations are injected, CopySVGTranslation runs a **preparation pipeline**
(`SvgPreparationPipeline`) that normalizes an arbitrary SVG into the canonical
"one `<switch>` per translatable text, one `<tspan>` per text segment, unique IDs,
normalized `systemLanguage`" shape that extraction and injection rely on.

Preparation is implicit during `inject()` and `extract_and_inject()`. You can also
run it standalone via `service.prepare_only()` to clean a file for manual editing
or another tool.

## The ordered steps

The pipeline runs these `PreparationStep`s in order. Each receives a shared
`PreparationContext` (the tree, root, config, and a shared `IdManager`).

| #   | Step                | Responsibility                                                                                                                 |
| --- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 1   | `LoadDocument`      | Parse the file (`SvgDocument.load`) and ensure a default SVG namespace.                                                        |
| 2   | `ValidateStructure` | Reject unsupported constructs: `<tref>`, over-complex CSS, IDs in CSS, `$N` placeholders.                                      |
| 3   | `NormalizeTspans`   | Flatten nested `<tspan>` (per `nested_strategy`); wrap loose text directly under `<text>` into a `<tspan>`.                    |
| 4   | `AssignIds`         | Register existing IDs; assign `trsvgN` IDs to `<text>`/`<tspan>` lacking one (when `assign_missing_ids`).                      |
| 5   | `WrapTspans`        | Ensure `<tspan>` children are well-formed for translation.                                                                     |
| 6   | `WrapTextElements`  | Reject `$N` text, normalize `systemLanguage`, wrap each `<text>` in a `<switch>`, move style up, keep only `<tspan>` children. |
| 7   | `SplitLanguages`    | Expand comma-separated `systemLanguage` values (e.g. `en,fr`) into cloned `<text>` nodes.                                      |
| 8   | `ReorderTexts`      | Sort each switch's `<text>` children deterministically; the fallback (no `systemLanguage`) is placed last.                     |

The order matters: IDs are assigned before wrapping (so wrapped switches get their
own IDs), and languages are split before the final reorder.

## Why preparation is needed

Real-world SVGs from tools like Wikimedia's charts often:

-   put bare text outside any `<switch>`,
-   omit `id` attributes,
-   use comma-separated `systemLanguage` lists,
-   embed nested `<tspan>` styling,
-   or use non-canonical language tags.

Preparation turns all of these into the single shape the rest of the library
expects, so extraction and injection logic stays simple and uniform.

## Running it standalone

```python
from CopySVGTranslation import SVGTranslationService

service = SVGTranslationService()
result = service.prepare_only("original.svg", output="prepared/original.svg")

if result.success:
    prepared_tree = result.data
```

When `output` is omitted, the prepared `ElementTree` is returned in `result.data`
without touching disk.

## Related

-   [nested-structures.md](nested-structures.md) — how nested `<tspan>`/`a` handling
    (`nested_strategy`) works during normalization.
-   [injection.md](injection.md) — preparation as step 1 of injection.
