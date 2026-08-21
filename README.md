# CopySVGTranslation

[![PyPI Version](https://img.shields.io/pypi/v/CopySVGTranslation.svg?style=flat-square)](https://pypi.org/project/CopySVGTranslation/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?style=flat-square)](https://www.python.org/downloads/)

**Extract multilingual text from SVG files and inject translations into other SVGs.**

CopySVGTranslation works with SVG documents that use `<switch>` elements and `systemLanguage` attributes. The public entry point, `SVGTranslationService`, coordinates extraction, injection, preparation, nested-structure repair, and JSON mapping I/O through one consistent result type.

---

## Features

-   Extract language variants from `<switch>` elements into a `TranslationMapping`.
-   Inject missing translations or update existing language nodes.
-   Prepare SVGs by normalizing structure, IDs, and language tags before translation work.
-   Inspect and repair nested `<tspan>` / `<a>` structures independently of extraction and injection.
-   Save and load JSON translation mappings.
-   Configure matching, overwrite, output, and nested-node behavior in `TranslationConfig`.
-   Receive uniform `OperationResult` objects instead of unhandled lower-level errors when using the service facade.

---

## Installation

CopySVGTranslation requires **Python 3.10 or later**.

```bash
pip install CopySVGTranslation
```

---

## Quick Start

Create one service instance and use it for the operation you need. The example below extracts Arabic and French text from one SVG and applies it to another SVG, saving the completed document.

```python
from pathlib import Path

from CopySVGTranslation import SVGTranslationService, TranslationConfig

config = TranslationConfig(
    case_insensitive=True,
    overwrite_translations=False,
    pretty_print=True,
    nested_strategy="raise",
    mapping_output_dir=Path("mappings"),
    output_dir=Path("translated"),
)
service = SVGTranslationService(config)

result = service.extract_and_inject(
    source="source.svg",
    output="target.svg",             # modified and saved in place
    save_mapping=True,                 # saved under mappings/
    save=True,
)

if not result.success:
    raise RuntimeError(f"{result.error_code}: {result.error}")

print(f"Inserted: {result.stats.inserted_translations}")
print(f"Updated: {result.stats.updated_translations}")
print(f"Skipped: {result.stats.skipped_translations}")
```

> `output_dir` is applied only when `output` is a bare filename. For example, `output="target-translated.svg"` resolves to `translated/target-translated.svg`, whereas `output="build/target.svg"` is used unchanged.

---

## `SVGTranslationService` at a Glance

`SVGTranslationService` is the high-level facade. Instantiate it with an optional `TranslationConfig`; omitting the configuration uses the package defaults.

```python
from CopySVGTranslation import SVGTranslationService

service = SVGTranslationService()
```

| Method                                                                | Purpose                                                               | Successful `data` payload |
| --------------------------------------------------------------------- | --------------------------------------------------------------------- | ------------------------- |
| `analyze_nested(svg_path)`                                            | Detect nested `<tspan>` / `<a>` structures without changing the file. | `list[str]` of findings   |
| `repair_nested(svg_path, *, output=None, strategy=None, save=True)`   | Repair nested structures using a selected strategy.                   | `RepairResult`            |
| `extract(svg_path, *, save_mapping=None)`                             | Read translations from an SVG.                                        | `TranslationMapping`      |
| `inject(svg_path, mapping, *, output=None, save=None)`                | Apply a mapping to an SVG.                                            | `InjectorData`            |
| `extract_and_inject(source, output, *, save_mapping=None, save=None)` | Extract from one SVG and inject into the single output target.        | `InjectorData`            |
| `prepare_only(svg_path, *, output=None)`                              | Normalize a document without injecting translations.                  | `lxml.etree._ElementTree` |
| `load_mapping(path)`                                                  | Read a saved JSON mapping.                                            | `TranslationMapping`      |
| `save_mapping(mapping, path)`                                         | Write a `TranslationMapping` to JSON.                                 | `pathlib.Path`            |

The following sections show each supported use case in detail.

---

## Handle Results Consistently

Every public service method returns an `OperationResult`. Check `success` before consuming `data`; on a failure, inspect `error`, `error_code`, and any non-fatal `warnings`.

```python
result = service.extract("source.svg")

if result.success:
    mapping = result.data
    for warning in result.warnings:
        print(f"Warning: {warning}")
else:
    print(f"Operation failed ({result.error_code}): {result.error}")
```

| Field        | Meaning                                                                                     |
| ------------ | ------------------------------------------------------------------------------------------- |
| `success`    | `True` when the operation completed successfully.                                           |
| `data`       | The method-specific payload, or `None` on failure.                                          |
| `stats`      | `InjectorStats` for successful injection workflows and some injection failures.             |
| `error`      | Human-readable error text when `success` is `False`.                                        |
| `error_code` | Machine-readable failure identifier when available.                                         |
| `warnings`   | Non-fatal issues, such as a mapping that was extracted successfully but could not be saved. |

---

## Extract Translations

Use `extract()` to collect the translations already present in a multilingual SVG. It accepts either a `str` or `pathlib.Path`.

```python
from CopySVGTranslation import SVGTranslationService

service = SVGTranslationService()
result = service.extract("examples/source_multilingual.svg")

if result.success:
    mapping = result.data
    print(mapping.to_json())
```

### Save the extracted mapping

Pass a path to write the mapping to an explicit location.

```python
result = service.extract(
    "source.svg",
    save_mapping="artifacts/source-mapping.json",
)
```

Alternatively, pass `True` to write `<source filename>.json` under `TranslationConfig.mapping_output_dir`; when it is unset, the conventional destination is `<source parent>/data/<source filename>.json`.

```python
from pathlib import Path
from CopySVGTranslation import SVGTranslationService, TranslationConfig

service = SVGTranslationService(
    TranslationConfig(mapping_output_dir=Path("mappings")),
)
result = service.extract("source.svg", save_mapping=True)
# Successful extraction writes mappings/source.svg.json.
```

If extraction succeeds but the mapping cannot be saved, `success` remains `True` and the save issue is placed in `result.warnings`. When `save_mapping=True`, `mapping_output_dir` takes precedence; otherwise the service uses the conventional `data/` directory beside the source SVG.

### Extract after in-memory preparation

For an SVG that does not yet contain the structure expected by extraction, enable preparation before extraction.

```python
from CopySVGTranslation import SVGTranslationService, TranslationConfig

service = SVGTranslationService(
    TranslationConfig(prepare_before_extraction=True),
)
result = service.extract("unprepared.svg")
```

This prepares the document in memory before extraction; it does **not** write a prepared SVG. Use `prepare_only()` when you want to save the preparation result.

---

## Inject Translations

Use `inject()` to apply a `TranslationMapping` or a compatible dictionary to a target SVG. By default, the modified XML tree is returned in memory and no file is written.

```python
from CopySVGTranslation import SVGTranslationService

service = SVGTranslationService()
mapping = {
    "new": {
        "hello": {"ar": "مرحبا", "fr": "Bonjour"},
        "music in 2020": {
            "ar": "الموسيقى في عام 2020",
            "fr": "La musique en 2020",
        },
    },
}

result = service.inject("target.svg", mapping)

if result.success:
    tree = result.data.tree
    print(result.stats.inserted_translations)
```

### Save an injected SVG

To write the generated document, provide an output path and set `save=True`.

```python
result = service.inject(
    "target.svg",
    mapping,
    output="translated/target.svg",
    save=True,
)
```

`save=None` follows `TranslationConfig.auto_save`. Whenever the effective value of `save` is `True`, `output` is required; otherwise the service returns a failed result with `error_code == "missing_output_path"`.

### Use a `TranslationMapping` object

The same method accepts a mapping object returned by `extract()` or loaded from JSON.

```python
extract_result = service.extract("source.svg")
if extract_result.success:
    inject_result = service.inject(
        "target.svg",
        extract_result.data,
        output="translated/target.svg",
        save=True,
    )
```

### Inspect injection statistics

Successful injection results expose `InjectorStats` through `result.stats`.

| Field                   | Meaning                                             |
| ----------------------- | --------------------------------------------------- |
| `processed_switches`    | Number of `<switch>` elements processed.            |
| `inserted_translations` | Language nodes created during the run.              |
| `updated_translations`  | Existing language nodes overwritten during the run. |
| `skipped_translations`  | Existing language nodes left unchanged.             |
| `all_languages_count`   | Total number of languages after injection.          |
| `new_languages_count`   | Number of newly added languages.                    |
| `languages_before`      | Languages present before injection.                 |
| `languages_after`       | Languages present after injection.                  |

---

## Extract and Inject in One Step

Use `extract_and_inject()` for the common workflow of copying translations from a source SVG to one output target SVG. The supplied `output` file is read, modified, and—when saving is enabled—overwritten in place. This in-place workflow intentionally does not apply `TranslationConfig.output_dir`. The method returns the injection result and carries forward any extraction warnings.

```python
from pathlib import Path
from CopySVGTranslation import SVGTranslationService, TranslationConfig

service = SVGTranslationService(
    TranslationConfig(mapping_output_dir=Path("mappings")),
)

result = service.extract_and_inject(
    source="source-multilingual.svg",
    output="target-default-language.svg",
    save_mapping=True,
    save=True,
)

if result.success:
    print(f"Created {result.stats.inserted_translations} translation node(s).")
else:
    print(result.error)
```

Set `save_mapping` to `False` or `None` when the intermediate JSON file is not needed. As with `inject()`, `save` defaults to `config.auto_save` when omitted.

---

## Prepare an SVG Without Translating It

`prepare_only()` runs the preparation pipeline without inserting any translations. This is useful when you want to clean an SVG before manual translation or before handing it to another tool.

```python
from CopySVGTranslation import SVGTranslationService

service = SVGTranslationService()
result = service.prepare_only(
    "original.svg",
    output="prepared/original.svg",
)

if result.success:
    prepared_tree = result.data
```

When `output` is supplied, the prepared document is written to that path. When it is omitted, the prepared `ElementTree` is available only in `result.data`.

---

## Analyze and Repair Nested Structures

Nested `<tspan>` and `<a>` nodes may require special handling. These operations are deliberately separate from `extract()` and `inject()`, so you can inspect or repair a document before proceeding.

### Analyze without modification

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

### Repair and save

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

| Strategy              | Behavior                                                                     |
| --------------------- | ---------------------------------------------------------------------------- |
| `raise`               | Stops when nested `<tspan>` structures are encountered. This is the default. |
| `flatten`             | Concatenates nested text into a single `<tspan>`.                            |
| `preserve_style`      | Converts nested styled spans to sibling spans while retaining styling.       |
| `split_nested_tspans` | Alias behavior for `preserve_style`.                                         |

`RepairResult` reports `len_tags_before_fix`, `len_tags_after_fix`, the derived `len_tags_fixed`, and any warnings.

---

## Save and Load JSON Mappings

The service exposes explicit mapping helpers for workflows that persist translations separately from SVG operations.

```python
from pathlib import Path
from CopySVGTranslation import SVGTranslationService, TranslationMapping

service = SVGTranslationService()
mapping = TranslationMapping(new={"hello": {"ar": "مرحبا"}})

save_result = service.save_mapping(mapping, Path("mappings/hello.json"))
if not save_result.success:
    raise RuntimeError(save_result.error)

load_result = service.load_mapping("mappings/hello.json")
if load_result.success:
    restored_mapping = load_result.data
```

`save_mapping()` returns the written path in `data`. Parent directories are created when `TranslationConfig.create_parents` is `True`, which is the default.

---

## Translation Mapping Format

`inject()` accepts either a `TranslationMapping` instance or a dictionary with the following compatible shape.

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

| Key            | Purpose                                                             |
| -------------- | ------------------------------------------------------------------- |
| `new`          | Normalized source text mapped to language-code/translation pairs.   |
| `title_new`    | Templates for titles containing years, with a `{year}` placeholder. |
| `tspans_by_id` | Diagnostic map of tspan IDs to default text.                        |
| `meta`         | Extra metadata.                                                     |
| `error`        | Mapping-level error text, when present.                             |

Call `mapping.to_json()` to obtain a serializable dictionary.

---

## Configuration

`TranslationConfig` controls the behavior of every service collaborator. Create a modified configuration with `with_updates()` rather than changing an existing instance in place.

```python
from pathlib import Path
from CopySVGTranslation import TranslationConfig

config = TranslationConfig(
    # Matching and injection
    case_insensitive=True,
    overwrite_translations=False,
    pretty_print=True,

    # Nested <tspan> / <a> handling
    nested_strategy="preserve_style",

    # Title and fallback behavior
    enable_year_titles=True,
    create_lang_template=False,
    fallback_to_default_text=False,

    # File output
    auto_save=False,
    output_dir=Path("out"),
    mapping_output_dir=Path("mappings"),
    create_parents=True,

    # Parsing and preparation
    remove_blank_text=True,
    normalize_languages=True,
    assign_missing_ids=True,
    prepare_before_extraction=False,
    sort_switches=False,

    # Diagnostics
    collect_warnings=True,
)

updated_config = config.with_updates(overwrite_translations=True)
```

| Group                     | Options                                                                                                        |
| ------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Matching                  | `case_insensitive`                                                                                             |
| Injection                 | `overwrite_translations`, `pretty_print`, `fallback_to_default_text`                                           |
| Nested content            | `nested_strategy`                                                                                              |
| Title handling            | `enable_year_titles`, `create_lang_template`                                                                   |
| Output                    | `auto_save`, `output_dir`, `mapping_output_dir`, `create_parents`                                              |
| Parsing and preparation   | `remove_blank_text`, `normalize_languages`, `assign_missing_ids`, `prepare_before_extraction`, `sort_switches` |
| Diagnostics and extension | `collect_warnings`, `extra`                                                                                    |

---

## Concrete SVG Example

Given a source SVG containing language variants:

```xml
<svg xmlns="http://www.w3.org/2000/svg">
  <switch>
    <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">مرحبا</tspan></text>
    <text id="t0-fr" systemLanguage="fr"><tspan id="t0-fr">Bonjour</tspan></text>
    <text id="t0"><tspan id="t0">Hello</tspan></text>
  </switch>
</svg>
```

and a target SVG with only the default text:

```xml
<svg xmlns="http://www.w3.org/2000/svg">
  <switch>
    <text id="t0"><tspan id="t0">Hello</tspan></text>
  </switch>
</svg>
```

running `extract_and_inject(source, output, save=True)` creates the Arabic and French language nodes in the output document and saves them back to that same file. Whether existing language nodes are replaced or preserved is controlled by `overwrite_translations`.

---

## Testing

```bash
python -m pytest tests -v
```

---

## License
