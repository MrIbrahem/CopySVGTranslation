
[![PyPi Version](https://img.shields.io/pypi/v/CopySVGTranslation.svg?style=flat-square)](https://pypi.org/project/CopySVGTranslation/)

# CopySVGTranslation

**Extract translations from multilingual SVG files and inject them into others.**

CopySVGTranslation is a Python library designed for working with SVG files that use the `<switch>` element and `systemLanguage` attributes for internationalization. It extracts translation mappings from source SVGs and injects them into target SVGs while preserving structure, IDs, and styling.

Ideal for projects that manage large collections of translated diagrams, charts, or illustrations (e.g. Wikimedia-style SVG translation workflows).

---

## Features

- **Extraction** – Pull language variants from `<switch>` elements into a structured `TranslationMapping`
- **Injection** – Apply translations to target SVGs, creating or updating language nodes
- **Preparation pipeline** – Normalize structure before injection:
  - Wrap loose text in `<tspan>`
  - Assign unique `trsvgN` IDs
  - Split comma-separated `systemLanguage` values
  - Handle nested `<tspan>` / `<a>` elements
  - Reorder children deterministically
- **Nested tspan strategies** – `raise`, `flatten`, or `preserve_style` / `split_nested_tspans`
- **Year-title handling** – Special support for titles containing 4-digit years (e.g. “COVID-19 pandemic 2020”)
- **Configurable matching** – Match segments by tspan ID (preferred) or by position
- **Clean public API** – High-level `SVGTranslationService` + lower-level components
- **Legacy compatibility** – Thin wrappers for older function-style APIs (deprecated)

---

## Installation

```bash
pip install CopySVGTranslation
# or from source
pip install -e .
```

**Requirements**
- Python 3.10+
- `lxml`

---

## Quick Start

### Extract translations

```python
from pathlib import Path
from CopySVGTranslation import SVGTranslationService, TranslationConfig

config = TranslationConfig(
    case_insensitive=True,
    enable_year_titles=True,
)

service = SVGTranslationService(config)

result = service.extract("source.svg", save_mapping=True)

if result.success:
    mapping = result.data
    print(f"Found {len(mapping.new)} source strings")
    print(mapping.to_json())
else:
    print("Extraction failed:", result.error)
```

### Inject translations

```python
result = service.inject(
    svg_path="target.svg",
    mapping=mapping,               # TranslationMapping or dict
    output="output.svg",
    save=True,
)

if result.success:
    stats = result.stats
    print(f"Inserted: {stats.inserted_translations}")
    print(f"Updated:  {stats.updated_translations}")
    print(f"Skipped:  {stats.skipped_translations}")
    print(f"New languages: {stats.languages_after}")
else:
    print("Injection failed:", result.error)
```

### One-shot: extract + inject

```python
result = service.extract_and_inject(
    source="source.svg",
    target="target.svg",
    output="result.svg",
    save=True,
    save_mapping=Path("mapping.json"),
)
```

### Prepare only (normalize structure)

```python
result = service.prepare_only("messy.svg", output="cleaned.svg")
```

---

## Configuration

All behaviour is controlled by `TranslationConfig`:

```python
from CopySVGTranslation import TranslationConfig
from pathlib import Path

config = TranslationConfig(
    # Matching
    case_insensitive=True,

    # Injection
    overwrite=False,                 # update existing language nodes?
    pretty_print=True,

    # Nested <tspan> handling
    nested_strategy="raise",         # "raise" | "flatten" | "preserve_style" | "split_nested_tspans"

    # Titles
    enable_year_titles=True,

    # I/O
    auto_save=False,
    output_dir=Path("out"),
    mapping_output_dir=Path("mappings"),
    create_parents=True,

    # Preparation
    remove_blank_text=True,
    normalize_languages=True,
    assign_missing_ids=True,
    sort_switches=False,

    # Diagnostics
    collect_warnings=True,
)
```

Create a modified copy with:

```python
new_config = config.with_updates(overwrite=True, nested_strategy="preserve_style")
```

---

## Core Concepts

| Concept | Description |
|---------|-------------|
| `TranslationMapping` | Main data structure: `new` (source → {lang: text}), optional `title_new` for year templates |
| `TranslationEntry` | One source string + its per-language translations |
| `TextNode` / `SwitchNode` | Thin domain wrappers around SVG `<text>` and `<switch>` elements |
| `OperationResult[T]` | Uniform success/error container with optional stats and warnings |
| Preparation Pipeline | Ordered steps that make an SVG translation-ready |

### Nested tspan strategies

| Strategy | Behaviour |
|----------|-----------|
| `raise` | Raise `SvgNestedTspanError` (default, safest) |
| `flatten` | Concatenate all nested text into a single tspan |
| `preserve_style` / `split_nested_tspans` | Convert nested styled tspans into sibling tspans (preferred for quality) |

---

## High-level Architecture

```
CopySVGTranslation/
├── service.py          # Public facade (SVGTranslationService)
├── config.py           # TranslationConfig
├── core/               # Domain models (Mapping, TextNode, SwitchNode)
├── extraction/         # Extractors + matching strategies
├── injection/          # Injectors, ID management, switch processing
├── preparation/        # Pre-injection pipeline (normalize, IDs, wrap, split…)
├── nested/             # Nested tspan detection & fixing
├── titles/             # Year-title special handling
├── io/                 # SVG document & mapping persistence
├── legacy/             # Deprecated function-style API
└── utils/              # Text & XML helpers
```

---

## Public API (selected)

```python
from CopySVGTranslation import (
    # Recommended entry point
    SVGTranslationService,

    # Configuration & data
    TranslationConfig,
    TranslationMapping,
    TranslationEntry,

    # Lower-level components
    SVGTranslationExtractor,
    SVGTranslationInjector,

    # Nested helpers
    NestedTspanDetector,
    NestedTspanFlattener,
    MatchFixNestedTags,
)
```

---

## Error Handling

All high-level operations return an `OperationResult`:

```python
result = service.extract("file.svg")

if result.success:
    data = result.data
    for warning in result.warnings:
        print("Warning:", warning)
else:
    print(result.error_code, result.error)
```

Typed exceptions (e.g. `SvgNestedTspanError`, `SvgStructureError`, `MappingError`) are raised internally and mapped to results at the service boundary.

---

## Legacy API (deprecated)

```python
from CopySVGTranslation.legacy import extract, inject_file_tree

# Still works but emits DeprecationWarning
mapping = extract("source.svg")
tree = inject_file_tree(inject_file="target.svg", mapping=mapping, save_path="out.svg")
```

Prefer `SVGTranslationService` for new code.

---

## Development

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests (once available)
pytest

# Type checking
mypy CopySVGTranslation
```

---

## License

[Add your license here – e.g. MIT, Apache-2.0, GPL-3.0]

---

## Related

This package is used by the **copy-svg-langs** project for bulk SVG translation workflows.
