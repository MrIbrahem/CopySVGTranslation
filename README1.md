# SVG Translation Tool

[![PyPi Version](https://img.shields.io/pypi/v/CopySVGTranslation.svg?style=flat-square)](https://pypi.org/project/CopySVGTranslation/)

This tool extracts multilingual text pairs from SVG files and applies translations to other SVG files by inserting missing `<text systemLanguage="XX">` blocks.

## Installation

This tool requires Python 3.10+. Install the lightweight core dependencies with:

```bash
pip install CopySVGTranslation
```

## Quick Start

The recommended API uses the **class-based** `SVGTranslationExtractor` and `SVGTranslationInjector` classes.

### Extract translations from an SVG

```python
from pathlib import Path
from CopySVGTranslation import SVGTranslationExtractor, TranslationConfig

config = TranslationConfig(
    case_insensitive = True,
    overwrite = False,
    pretty_print = None,
)
extractor = SVGTranslationExtractor(config)

result = extractor.extract(Path("examples/source_multilingual.svg"))

if not result.error:
    print(result.to_json())
    # {
    #     "new": {"hello": {"ar": "مرحبا", "fr": "Bonjour"}, ...},
    #     "tspans_by_id": {...},
    #     "title_new": {...},
    # }
```

### Extract from an SVG without `<switch>` elements

By default, extraction reads existing `<switch>` elements only. To prepare an SVG in memory before extraction, enable `prepare_before_extraction`. The preparation pipeline wraps eligible `<text>` elements in `<switch>` blocks, normalizes `<tspan>` content, and assigns missing IDs without modifying the source file.

```python
from CopySVGTranslation import SVGTranslationExtractor, TranslationConfig

extractor = SVGTranslationExtractor(
    TranslationConfig(prepare_before_extraction=True),
)
mapping = extractor.extract("diagram-without-switches.svg")
```

### Inject translations into an SVG

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
    }
}

result = injector.inject(
    inject_file=Path("examples/target_missing_translations.svg"),
    mapping=translations,
    save_path=Path("translated/target.svg"),
    save_result=True,
)

if not result.inject_stats.error:
    print(f"Inserted: {result.inject_stats.inserted_translations}")
    print(f"Updated:  {result.inject_stats.updated_translations}")
    print(f"Skipped:  {result.inject_stats.skipped_translations}")
    print(f"Languages: {result.inject_stats.all_languages_count}")
```

## API Reference

### `SVGTranslationExtractor`

The primary class for extracting translation data from SVG files.

```python
from CopySVGTranslation import SVGTranslationExtractor, TranslationConfig
config = TranslationConfig(
    case_insensitive = True,
    overwrite = False,
    pretty_print = None,
)
extractor = SVGTranslationExtractor(config)

result: TranslationMapping = extractor.extract(
    source_file: str | Path,
)
```

**Parameters:**

| Parameter          | Type          | Default | Description                                                                |
| ------------------ | ------------- | ------- | -------------------------------------------------------------------------- |
| `source_file`      | `str \| Path` | —       | Path to the SVG file to process.                                           |
| `case_insensitive` | `bool`        | `True`  | If `True`, default text keys are lowercased for case-insensitive matching. |

**Returns:** `TranslationMapping` — a dataclass with the following fields:

| Field          | Type                        | Description                                                      |
| -------------- | --------------------------- | ---------------------------------------------------------------- |
| `new`          | `dict[str, dict[str, str]]` | Mapping of normalized source text → language code → translation. |
| `tspans_by_id` | `dict[str, str]`            | Mapping of `<tspan>` ID → text content.                          |
| `title_new`    | `dict[str, Any]`            | New-format title translations.                                   |
| `meta`         | `dict[str, Any]`            | Diagnostic metadata.                                             |
| `error`        | `str`                       | Error message if extraction failed, empty string on success.     |

Use `result.to_json()` to get a plain dictionary suitable for JSON serialization.

---

### `SVGTranslationInjector`

The primary class for injecting translations into SVG files.

```python
from CopySVGTranslation import SVGTranslationInjector, TranslationConfig

config = TranslationConfig(
    case_insensitive: bool = True,
    overwrite: bool = False,
    pretty_print: bool | None = None,
)
injector = SVGTranslationInjector(config)

result: InjectorData = injector.inject(
    inject_file: Path | str,
    mapping: Mapping | None = None,
    save_path: Path | None = None,
    save_result: bool = False,
)
```

**Constructor Parameters:**

| Parameter          | Type   | Default | Description                                                                       |
| ------------------ | ------ | ------- | --------------------------------------------------------------------------------- |
| `case_insensitive` | `bool` | `True`  | If `True`, translation lookups are case-insensitive.                              |
| `overwrite`        | `bool` | `False` | If `True`, existing language nodes are updated in place instead of being skipped. |
| `pretty_print`     | `bool` | `True`  | If `True`, the output SVG is formatted with indentation.                          |

**`inject()` Parameters:**

| Parameter     | Type              | Default | Description                                                     |
| ------------- | ----------------- | ------- | --------------------------------------------------------------- |
| `inject_file` | `Path \| str`     | —       | Path to the SVG file to inject translations into.               |
| `mapping`     | `Mapping \| None` | `None`  | Translation mapping dictionary (see [Data Model](#data-model)). |
| `save_path`   | `Path \| None`    | `None`  | Output file path when `save_result=True`.                       |
| `save_result` | `bool`            | `False` | If `True`, writes the modified SVG to `save_path`.              |

**Returns:** `InjectorData` — a dataclass with the following fields:

| Field          | Type                         | Description                                  |
| -------------- | ---------------------------- | -------------------------------------------- |
| `tree`         | `etree._ElementTree \| None` | The parsed (and possibly modified) SVG tree. |
| `inject_stats` | `InjectorStats`              | Statistics about the injection run.          |

**`InjectorStats` fields:**

| Field                   | Type        | Description                                                 |
| ----------------------- | ----------- | ----------------------------------------------------------- |
| `all_languages_count`         | `int`       | Total number of languages in the SVG after injection.       |
| `new_languages_count`         | `int`       | Number of new languages added.                              |
| `processed_switches`    | `int`       | Number of `<switch>` elements processed.                    |
| `inserted_translations` | `int`       | Number of new `<text>` nodes inserted.                      |
| `skipped_translations`  | `int`       | Number of existing translations skipped (not overwritten).  |
| `updated_translations`  | `int`       | Number of existing translations updated in place.           |
| `languages_before`      | `list[str]` | Sorted list of language codes before injection.             |
| `languages_after`       | `list[str]` | Sorted list of newly added language codes.                  |
| `error`                 | `str`       | Error message if injection failed, empty string on success. |

Use `result.inject_stats.to_json()` to get a plain dictionary of the stats.

---

### `TranslationMapping`

Dataclass returned by `SVGTranslationExtractor.extract()`. See the extractor documentation above for field details.

### `InjectorData`

Dataclass returned by `SVGTranslationInjector.inject()`. See the injector documentation above for field details.

---

### Legacy (Deprecated) Functions

> **⚠️ Deprecation Notice:** The function-based `extract()` and `inject()` APIs are deprecated and will be removed in a future release. Migrate to `SVGTranslationExtractor` and `SVGTranslationInjector` respectively.

#### `extract()` _(deprecated)_

```python
from CopySVGTranslation import extract

# Deprecated — use SVGTranslationExtractor instead
translations = extract(
    source_file=Path("arabic.svg"),
    case_insensitive=True,
)
```

**Migration:**

```python
# Before (deprecated)
from CopySVGTranslation import extract
translations = extract(source_file=Path("arabic.svg"), case_insensitive=True)

# After (recommended)
from CopySVGTranslation import SVGTranslationExtractor, TranslationConfig
config = TranslationConfig(
    case_insensitive = True,
    overwrite = False,
    pretty_print = None,
)
extractor = SVGTranslationExtractor(config)
result = extractor.extract(Path("arabic.svg"))
translations = result.to_json() if not result.error else None
```

#### `inject_file_tree()` _(deprecated)_

```python
from CopySVGTranslation import inject_file_tree

# Deprecated — use SVGTranslationInjector instead
tree, stats = inject_file_tree(
    inject_file=Path("target.svg"),
    mapping=translations,
    output_dir=Path("./translated"),
    save_result=True,
    return_stats=True,
)
```

**Migration:**

```python
# Before (deprecated)
from CopySVGTranslation import inject_file_tree
tree, stats = inject_file_tree(
    inject_file=Path("target.svg"),
    mapping=translations,
    save_path=Path("translated/target.svg"),
    return_stats=True,
    save_result=True,
)

# After (recommended)
from CopySVGTranslation import SVGTranslationInjector, TranslationConfig
config = TranslationConfig(case_insensitive=True, overwrite=False)
injector = SVGTranslationInjector(config)
result = injector.inject(
    inject_file=Path("target.svg"),
    mapping=translations,
    save_path=Path("translated/target.svg"),
    save_result=True,
)
tree = result.tree
stats = result.inject_stats.to_json()
```

## Data Model

The extractor produces a JSON document with these top-level keys:

```json
{
    "new": {
        "normalized english text": {
            "ar": "Arabic translation",
            "fr": "French translation"
        }
    },
    "tspans_by_id": {
        "tspan-id": "Text content"
    },
    "title_new": {
        "text without year": {
            "ar": "...",
            "fr": "..."
        }
    }
}
```

| Key            | Description                                                                  |
| -------------- | ---------------------------------------------------------------------------- |
| `new`          | Primary mapping of normalized source text → language code → translation.     |
| `title`        | Title-like entries (text ending with a 4-digit year) with the year stripped. |
| `title_new`    | New-format title translations preserving additional metadata.                |
| `tspans_by_id` | Mapping of `<tspan>` element IDs to their text content.                      |

Older exports may omit the wrapper and look like `{"english": {"ar": "…"}}`. The injector transparently accepts both structures, but the recommended format is the nested layout shown above.

## Extract Example

### Input SVG (arabic.svg)

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

### Python code

```python
from pathlib import Path
from CopySVGTranslation import SVGTranslationExtractor, TranslationConfig

config = TranslationConfig(
    case_insensitive = True,
    overwrite = False,
    pretty_print = None,
)

extractor = SVGTranslationExtractor(config)

result = extractor.extract(Path("arabic.svg"))
print(result.to_json())
```

### Extracted JSON

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

## Injection Example

### Input SVG (target.svg)

```xml
<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <switch>
      <text id="t0">
          <tspan id="t0">Hello</tspan>
      </text>
  </switch>
  <switch>
      <text id="t1">
          <tspan id="t1">Music in 2020</tspan>
      </text>
  </switch>
</svg>
```

### Python code

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
        "hello": {"ar": "مرحبا", "fr": "Bonjour"},
        "music in 2020": {"ar": "الموسيقى في عام 2020", "fr": "La musique en 2020"},
    }
}

result = injector.inject(
    inject_file=Path("target.svg"),
    mapping=translations,
    save_path=Path("translated/target.svg"),
    save_result=True,
)

print(f"Inserted: {result.inject_stats.inserted_translations}")
print(f"Languages: {result.inject_stats.all_languages_count}")
```

### Output SVG (translated/target.svg)

```xml
<?xml version='1.0' encoding='utf-8'?>
<svg xmlns="http://www.w3.org/2000/svg">
  <switch>
    <text id="t0">
      <tspan id="t0">Hello</tspan>
    </text>
    <text id="t0-ar" systemLanguage="ar">
      <tspan id="t0-ar">مرحبا</tspan>
    </text>
    <text id="t0-fr" systemLanguage="fr">
      <tspan id="t0-fr">Bonjour</tspan>
    </text>
  </switch>
  <switch>
    <text id="t1">
      <tspan id="t1">Music in 2020</tspan>
    </text>
    <text id="t1-ar" systemLanguage="ar">
      <tspan id="t1-ar">الموسيقى في عام 2020</tspan>
    </text>
    <text id="t1-fr" systemLanguage="fr">
      <tspan id="t1-fr">La musique en 2020</tspan>
    </text>
  </switch>
</svg>
```

## Testing

Run the unit tests:

```bash
python -m pytest tests -v
```

## Implementation Details

### Text Normalization

The tool normalizes text by:

-   Trimming leading and trailing whitespace
-   Replacing multiple internal whitespace characters with a single space
-   Optionally converting to lowercase for case-insensitive matching

### ID Generation

When adding new translation nodes, the tool generates unique IDs by:

-   Taking the existing ID and appending the language code (e.g., `text2213` becomes `text2213-ar`)
-   If the generated ID already exists, appending a numeric suffix until unique (e.g., `text2213-ar-1`)

## Error Handling

The tool includes comprehensive error handling for:

-   Missing input files
-   Invalid XML structure
-   Missing required attributes
-   File permission issues
-   Nested `<tspan>` structures (raises `SvgNestedTspanError`)
-   Invalid SVG structures like `<tref>` elements (raises `SvgStructureError`)
