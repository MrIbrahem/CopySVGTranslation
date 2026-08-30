# Getting Started

This guide covers installing CopySVGTranslation and running the most common
workflows. The library targets **multilingual SVG files** that use `<switch>`
elements with per-language `<text systemLanguage="XX">` children (see
[architecture.md](architecture.md)).

## Installation

Requires **Python 3.11+** and `lxml`.

```bash
pip install CopySVGTranslation
```

For development from source:

```bash
poetry install
poetry run pytest        # run the test suite
```

## The one thing to import

```python
from CopySVGTranslation import SVGTranslationService, TranslationConfig, TranslationMapping
```

`SVGTranslationService` is the only supported entry point. Everything you need
goes through it, and every method returns an `OperationResult` (see
[data-models.md](data-models.md)).

## Five-minute tour

### 1. Copy translations from one SVG to another

```python
from CopySVGTranslation import SVGTranslationService

service = SVGTranslationService()
result = service.extract_and_inject(
    source="source-multilingual.svg",
    output="target-default-language.svg",
    save=True,
)

if result.success:
    print(f"Inserted {result.stats.inserted_translations} translation node(s).")
else:
    print(result.error)
```

### 2. Extract to JSON, re-apply later

```python
result = service.extract("source.svg", save_mapping=True)
mapping = result.data                       # TranslationMapping
service.inject("target.svg", mapping, output="out.svg", save=True)
```

### 3. Check switch ordering before re-uploading to Commons

```python
checked = service.check_switches_sorted("diagram.svg")
if checked.success and not checked.data:
    service.sort_switches("diagram.svg", output="fixed/diagram.svg")
```

See [switch-ordering.md](switch-ordering.md).

### 4. Repair nested `<tspan>` / `<a>` structures

```python
result = service.repair_nested("diagram.svg", output="repaired/diagram.svg")
```

See [nested-structures.md](nested-structures.md).

## Configuration

Pass a `TranslationConfig` to the service constructor. Create variations with
`with_updates()` rather than mutating in place (the config is treated as
immutable by convention).

```python
from CopySVGTranslation import TranslationConfig

config = TranslationConfig(
    case_insensitive=True,
    overwrite_translations=False,
    nested_strategy="preserve_style",
    sort_switches=True,
)
service = SVGTranslationService(config)
```

The full option table is in the main `README.md` → **Configuration** section.

## Result handling pattern

Every public method follows the same shape:

```python
result = service.extract("source.svg")

if result.success:
    mapping = result.data
    for warning in result.warnings:
        print(f"Warning: {warning}")
else:
    print(f"Failed ({result.error_code}): {result.error}")
```

## Where to go next

-   [architecture.md](architecture.md) — how the pieces fit together.
-   [data-models.md](data-models.md) — `TranslationMapping`, `InjectorStats`, `OperationResult`.
-   [extraction.md](extraction.md) / [injection.md](injection.md) — the two core pipelines.
-   [preparation.md](preparation.md) — what "prepare" does and why.
-   [nested-structures.md](nested-structures.md) / [switch-ordering.md](switch-ordering.md) — maintenance operations.
