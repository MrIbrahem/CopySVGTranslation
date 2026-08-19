
# CopySVGTranslation

[![PyPI Version](https://img.shields.io/pypi/v/CopySVGTranslation.svg?style=flat-square)](https://pypi.org/project/CopySVGTranslation/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?style=flat-square)](https://www.python.org/downloads/)

**Extract multilingual text from SVG files and inject translations into others.**

CopySVGTranslation works with SVG files that use the `<switch>` element and `systemLanguage` attributes. It extracts translation pairs and inserts missing language variants while preserving structure, IDs, and styling.

---

## Features

- Extract translations from `<switch>` elements into a structured mapping
- Inject translations, creating or updating language nodes
- Preparation pipeline that normalizes SVG structure before injection
- Configurable handling of nested `<tspan>` / `<a>` elements
- Special support for titles containing 4-digit years
- Case-insensitive matching and language-tag normalization
- Clean class-based API + thin legacy compatibility layer

---

## Installation

Requires **Python 3.10+**.

```bash
pip install CopySVGTranslation
```

---

## Quick Start (Recommended)

The highest-level entry point is `SVGTranslationService`.

```python
from pathlib import Path
from CopySVGTranslation import SVGTranslationService, TranslationConfig

config = TranslationConfig(
    case_insensitive=True,
    overwrite=False,
    pretty_print=True,
    nested_strategy="raise",          # "raise" | "flatten" | "preserve_style"
    enable_year_titles=True,
)

service = SVGTranslationService(config)

# Extract
extract_result = service.extract("source.svg", save_mapping=True)
if extract_result.success:
    mapping = extract_result.data
    print(mapping.to_json())

# Inject
inject_result = service.inject(
    svg_path="target.svg",
    mapping=mapping,
    output="translated/target.svg",
    save=True,
)

if inject_result.success:
    stats = inject_result.stats
    print(f"Inserted: {stats.inserted_translations}")
    print(f"Updated:  {stats.updated_translations}")
    print(f"Skipped:  {stats.skipped_translations}")
    print(f"New languages: {stats.languages_after}")

# One-shot
result = service.extract_and_inject(
    source="source.svg",
    target="target.svg",
    output="result.svg",
    save=True,
)
```

You can also work directly with the lower-level classes (shown below).

---

## Lower-level API

### Extract translations

```python
from pathlib import Path
from CopySVGTranslation import SVGTranslationExtractor, TranslationConfig

config = TranslationConfig(case_insensitive=True)
extractor = SVGTranslationExtractor(config)

mapping = extractor.extract(Path("examples/source_multilingual.svg"))
print(mapping.to_json())
```

### Inject translations

```python
from pathlib import Path
from CopySVGTranslation import SVGTranslationInjector, TranslationConfig

config = TranslationConfig(
    case_insensitive=True,
    overwrite=False,
    pretty_print=True,
)
injector = SVGTranslationInjector(config)

translations = {
    "new": {
        "Hello": {"ar": "مرحبًا", "fr": "Bonjour"},
        "Music in 2020": {"ar": "الموسيقى في عام 2020", "fr": "La musique en 2020"},
    }
}

result = injector.inject(
    svg_path=Path("examples/target_missing_translations.svg"),
    mapping=translations,
    save_path=Path("translated/target.svg"),
    save=True,
)

if not result.inject_stats.error:
    print(f"Inserted: {result.inject_stats.inserted_translations}")
    print(f"Updated:  {result.inject_stats.updated_translations}")
    print(f"Skipped:  {result.inject_stats.skipped_translations}")
    print(f"Languages after: {result.inject_stats.all_languages_count}")
```

---

## Configuration

All behaviour is controlled by the immutable-style `TranslationConfig` dataclass:

```python
from pathlib import Path
from CopySVGTranslation import TranslationConfig

config = TranslationConfig(
    # Matching
    case_insensitive=True,

    # Injection
    overwrite=False,
    pretty_print=True,

    # Nested <tspan> handling
    nested_strategy="raise",          # "raise" | "flatten" | "preserve_style" | "split_nested_tspans"

    # Titles containing years
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
    prepare_before_extraction=False,  # Prepare SVG text in memory before extraction
    sort_switches=False,

    # Diagnostics
    collect_warnings=True,
)

# Create a modified copy
new_config = config.with_updates(overwrite=True, nested_strategy="preserve_style")
```

---

## API Reference

### `SVGTranslationService` (recommended)

High-level facade that wires extractor, injector, preparation and mapping I/O together.

| Method | Description |
|--------|-------------|
| `extract(svg_path, *, save_mapping=None)` | Extract → `OperationResult[TranslationMapping]` |
| `inject(svg_path, mapping, *, output=None, save=None)` | Inject → `OperationResult[InjectorData]` |
| `extract_and_inject(source, target, ...)` | Convenience one-shot |
| `prepare_only(svg_path, *, output=None)` | Run only the normalization pipeline |
| `load_mapping(path)` / `save_mapping(mapping, path)` | JSON mapping helpers |

### `SVGTranslationExtractor`

```python
extractor = SVGTranslationExtractor(config)
mapping: TranslationMapping = extractor.extract(source_file)
```

**Returns** a `TranslationMapping` with these fields:

| Field | Type | Description |
|-------|------|-------------|
| `new` | `dict[str, dict[str, str]]` | Normalized source text → `{lang: translation}` |
| `title_new` | `dict[str, dict[str, str]]` | Year-title templates (`{year}` placeholder) |
| `tspans_by_id` | `dict[str, str]` | Diagnostic map of tspan ID → default text |
| `meta` | `dict` | Extra metadata (e.g. header translations) |
| `error` | `str` | Non-empty only on failure |

Call `mapping.to_json()` for a plain serializable dict.

### `SVGTranslationInjector`

```python
injector = SVGTranslationInjector(config)
result: InjectorData = injector.inject(
    svg_path,
    mapping,
    save_path=None,
    save=False,
)
```

**`InjectorData`**

| Field | Type | Description |
|-------|------|-------------|
| `tree` | `etree._ElementTree \| None` | Modified SVG tree |
| `inject_stats` | `InjectorStats` | Run statistics |

**`InjectorStats`**

| Field | Type | Description |
|-------|------|-------------|
| `all_languages_count` | `int` | Total languages after injection |
| `new_languages_count` | `int` | Newly added languages |
| `processed_switches` | `int` | `<switch>` elements processed |
| `inserted_translations` | `int` | New language nodes created |
| `updated_translations` | `int` | Existing nodes overwritten |
| `skipped_translations` | `int` | Existing nodes left untouched |
| `languages_before` | `list[str]` | Languages present before |
| `languages_after` | `list[str]` | Newly added language codes |
| `error` | `str` | Non-empty on failure |

---

## Data Model

```json
{
  "new": {
    "music in 2020": {
      "ar": "الموسيقى في عام 2020",
      "fr": "La musique en 2020"
    },
    "hello": {
      "ar": "مرحبا",
      "fr": "Bonjour"
    }
  },
  "title_new": {
    "music in {year}": {
      "ar": "الموسيقى في عام {year}",
      "fr": "La musique en {year}"
    }
  },
  "tspans_by_id": {
    "t0": "Music in 2020",
    "t1": "Hello"
  },
  "meta": {},
  "error": ""
}
```

The injector accepts both the nested format above and older flat dictionaries.

---

## Concrete Examples

### Extraction

**Input** (`arabic.svg`):

```xml
<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <switch>
    <text id="t0-ar" systemLanguage="ar">
      <tspan id="t0-ar">الموسيقى في عام 2020</tspan>
    </text>
    <text id="t0-fr" systemLanguage="fr">
      <tspan id="t0-fr">La musique en 2020</tspan>
    </text>
    <text id="t0">
      <tspan id="t0">Music in 2020</tspan>
    </text>
  </switch>
  <switch>
    <text id="t1-ar" systemLanguage="ar">
      <tspan id="t1-ar">مرحبا</tspan>
    </text>
    <text id="t1-fr" systemLanguage="fr">
      <tspan id="t1-fr">Bonjour</tspan>
    </text>
    <text id="t1">
      <tspan id="t1">Hello</tspan>
    </text>
  </switch>
</svg>
```

**Result**:

```json
{
  "new": {
    "music in 2020": {
      "ar": "الموسيقى في عام 2020",
      "fr": "La musique en 2020"
    },
    "hello": {
      "ar": "مرحبا",
      "fr": "Bonjour"
    }
  },
  "tspans_by_id": {
    "t0": "Music in 2020",
    "t1": "Hello"
  },
  "title_new": {},
  "error": ""
}
```

### Injection

**Input** (`target.svg`):

```xml
<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <switch>
    <text id="t0"><tspan id="t0">Hello</tspan></text>
  </switch>
  <switch>
    <text id="t1"><tspan id="t1">Music in 2020</tspan></text>
  </switch>
</svg>
```

**Output** (after injection):

```xml
<?xml version='1.0' encoding='utf-8'?>
<svg xmlns="http://www.w3.org/2000/svg">
  <switch>
    <text id="t0"><tspan id="t0">Hello</tspan></text>
    <text id="t0-ar" systemLanguage="ar">
      <tspan id="t0-ar">مرحبا</tspan>
    </text>
    <text id="t0-fr" systemLanguage="fr">
      <tspan id="t0-fr">Bonjour</tspan>
    </text>
  </switch>
  <switch>
    <text id="t1"><tspan id="t1">Music in 2020</tspan></text>
    <text id="t1-ar" systemLanguage="ar">
      <tspan id="t1-ar">الموسيقى في عام 2020</tspan>
    </text>
    <text id="t1-fr" systemLanguage="fr">
      <tspan id="t1-fr">La musique en 2020</tspan>
    </text>
  </switch>
</svg>
```

---

## Nested `<tspan>` Strategies

| Strategy | Behaviour |
|----------|-----------|
| `raise` (default) | Raise `SvgNestedTspanError` |
| `flatten` | Concatenate all nested text into a single tspan |
| `preserve_style` / `split_nested_tspans` | Convert nested styled tspans into sibling tspans (keeps styling) |

---

## Legacy API (Deprecated)

> **⚠️ Deprecated** – will be removed in a future major release. Prefer `SVGTranslationService` or the class-based extractor/injector.

```python
from CopySVGTranslation.legacy import extract, inject_file_tree

# Old style
mapping = extract("source.svg", case_insensitive=True)
tree, stats = inject_file_tree(
    inject_file="target.svg",
    mapping=mapping,
    save_path="out.svg",
    save_result=True,
    return_stats=True,
)
```

**Migration**

```python
# Before
from CopySVGTranslation.legacy import extract
translations = extract("arabic.svg")

# After
from CopySVGTranslation import SVGTranslationService, TranslationConfig
service = SVGTranslationService(TranslationConfig(case_insensitive=True))
result = service.extract("arabic.svg")
translations = result.data.to_json() if result.success else None
```

---

## Implementation Notes

### Text Normalization
- Trim leading/trailing whitespace
- Collapse internal whitespace to a single space
- Optionally lower-case for case-insensitive keys

### ID Generation
- Prefer `base-lang` form (e.g. `trsvg12` → `trsvg12-ar`)
- On collision append a numeric suffix (`trsvg12-ar_1`, …)
- Missing IDs are automatically allocated as `trsvgN`

### Error Handling
Typed exceptions (`SvgNestedTspanError`, `SvgStructureError`, `SvgParseError`, `MappingError`, …) are raised by the lower layers.  
`SVGTranslationService` converts them into `OperationResult` so callers can handle success/failure uniformly.

---

## Testing

```bash
python -m pytest tests -v
```

---

## License

