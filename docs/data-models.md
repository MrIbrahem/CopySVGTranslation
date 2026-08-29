# Data Models

CopySVGTranslation uses a small set of dataclasses to move data between the
extraction, injection, and service layers. This document describes each one and
how to use it.

## TranslationMapping

The central data structure. Produced by extraction, consumed by injection.

```python
@dataclass(slots=True)
class TranslationMapping:
    new: dict[str, dict[str, str]]          # source text → {lang: translation}
    title_new: dict[str, dict[str, str]]    # year-title templates (advanced)
    tspans_by_id: dict[str, str]            # diagnostic: tspan id → default text
    meta: dict[str, Any]                    # extra metadata / diagnostics
    error: str | None                       # mapping-level error text
```

### Structure

```json
{
    "new": {
        "music in 2020": {
            "ar": "الموسيقى في عام 2020",
            "fr": "La musique en 2020"
        }
    },
    "title_new": {
        "music in {year}": {
            "ar": "الموسيقى في عام {year}",
            "fr": "La musique en {year}"
        }
    },
    "tspans_by_id": { "t0": "Music in 2020" },
    "meta": {},
    "error": ""
}
```

### Construction

You can build a mapping from a dict with the same shape:

```python
from CopySVGTranslation import TranslationMapping

mapping = TranslationMapping.from_any({
    "new": {"hello": {"ar": "مرحبا", "fr": "Bonjour"}},
})
# TranslationMapping is also accepted (returns itself)
same = TranslationMapping.from_any(mapping)
```

### Useful helpers

| Method                                              | Purpose                                                   |
| --------------------------------------------------- | --------------------------------------------------------- |
| `is_empty()`                                        | `True` when no `new` and no `title_new` entries.          |
| `all_languages()`                                   | Set of all language codes across `new` and `title_new`.   |
| `lookup(source, *, case_insensitive=True)`          | `{lang: text}` for a source string, or `{}`.              |
| `entries()`                                         | Iterate `TranslationEntry(source=..., translations=...)`. |
| `add(source, lang, text, *, case_insensitive=True)` | Add/replace one translation.                              |
| `merge(other, merge_keys=None)`                     | Merge another mapping in place.                           |
| `to_json()`                                         | Serializable dict (matches the JSON file format).         |

### Notes

-   `case_insensitive=True` (the default and the config default) stores and looks up
    source strings lowercased. Keep this consistent between extraction and injection.
-   `title_new` is only populated when year-aware title handling is enabled
    (`TranslationConfig.enable_year_titles`). It is rarely needed for simple
    translation copy.

## TranslationEntry

A single source string and its translations, yielded by `mapping.entries()`.

```python
@dataclass(slots=True, frozen=True)
class TranslationEntry:
    source: str
    translations: Mapping[str, str]

    def get(self, lang: str, default=None) -> str | None: ...
    def languages(self) -> set[str]: ...
```

## InjectorData

Returned (in `OperationResult.data`) by injection. Wraps the modified tree and
statistics.

```python
@dataclass
class InjectorData:
    tree: etree._ElementTree | None   # the modified SVG tree (None on failure)
    inject_stats: InjectorStats       # statistics for this run
    error: Error                      # error info when tree is None
```

Access the tree after a successful inject:

```python
result = service.inject("target.svg", mapping, output="out.svg", save=True)
if result.success:
    tree = result.data.tree
```

## InjectorStats

Counts produced during injection. Available as `result.stats` on any
successful/partial injection result.

| Field                                  | Meaning                                                          |
| -------------------------------------- | ---------------------------------------------------------------- |
| `processed_switches`                   | `<switch>` elements processed.                                   |
| `inserted_translations`                | Language nodes created this run.                                 |
| `updated_translations`                 | Existing nodes overwritten (when `overwrite_translations=True`). |
| `skipped_translations`                 | Existing nodes left unchanged.                                   |
| `all_languages_count`                  | Total languages present after injection.                         |
| `new_languages_count`                  | Languages added this run.                                        |
| `languages_before` / `languages_after` | Language codes present before/after.                             |

`has_changes()` returns `True` when any node was inserted, updated, or a new
language was added. Serialize with `to_json()`.

## Error

Internal error carrier inside `InjectorData.error`; holds an optional `code` and
human-readable `label`. You normally read failures from `OperationResult.error`
/ `error_code` instead.

## OperationResult

The uniform wrapper returned by **every** `SVGTranslationService` method.

```python
@dataclass(slots=True)
class OperationResult(Generic[TY]):
    success: bool
    data: TY | None = None
    stats: InjectorStats | None = None
    error: str | None = None
    error_code: str | None = None
    warnings: list[str] = field(default_factory=list)
```

Use the `ok()` / `fail()` constructors internally; callers just inspect fields:

```python
if result.success:
    payload = result.data
else:
    print(result.error_code, result.error)
```

`warnings` carries non-fatal issues (e.g. a mapping that extracted fine but could
not be saved), so a `success=True` result can still report partial issues.
