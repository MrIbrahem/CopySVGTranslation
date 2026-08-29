# Analyze and Repair Nested Structures

Nested `<tspan>` and `<a>` nodes may require special handling. These operations are deliberately separate from `extract()` and `inject()`, so you can inspect or repair a document before proceeding.

## Analyze without modification

`analyze_nested()` is read-only and returns XML snippets describing nested structures.

```python
result = service.analyze_nested("diagram.svg")

if result.success:
    if result.data:
        print("Nested structures found:")
        for finding in result.data:
            print(finding)
    else:
        print("No nested structures found.")
```

## Repair and save

`repair_nested()` uses the configured strategy by default. Because its default is `save=True`, provide an output path unless you explicitly set `save=False`.

```python
from CopySVGTranslation import SVGTranslationService, TranslationConfig

service = SVGTranslationService(
    TranslationConfig(nested_strategy="preserve_style"),
)
result = service.repair_nested(
    "diagram.svg",
    output="repaired/diagram.svg",
)

if result.success:
    repair = result.data
    print(f"Nested tags fixed: {repair.len_tags_fixed}")
    print(f"Before: {repair.len_tags_before_fix}")
    print(f"After: {repair.len_tags_after_fix}")
```

To repair only in memory, disable saving explicitly.

```python
result = service.repair_nested(
    "diagram.svg",
    strategy="flatten",
    save=False,
)
```

## Strategies

| Strategy              | Behavior                                                                     |
| --------------------- | ---------------------------------------------------------------------------- |
| `raise`               | Stops when nested `<tspan>` structures are encountered. This is the default. |
| `flatten`             | Concatenates nested text into a single `<tspan>`.                            |
| `preserve_style`      | Converts nested styled spans to sibling spans while retaining styling.       |
| `split_nested_tspans` | Alias behavior for `preserve_style`.                                         |

`RepairResult` reports `len_tags_before_fix`, `len_tags_after_fix`, the derived `len_tags_fixed`, and any warnings.
