# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CopySVGTranslation is a Python library for extracting multilingual text pairs from SVG files and applying translations by inserting `<text systemLanguage="XX">` blocks. It works with SVG files that use `<switch>` elements containing `<text>` nodes with `systemLanguage` attributes.

## Commands

### Running Tests

```bash
# Run all tests
python -m pytest tests -v

# Run a specific test file
python -m pytest tests/test_svgtranslate.py -v

# Run a specific test
python -m pytest tests/test_svgtranslate.py::test_extract -v
```

### Installation for Development

```bash
pip install -r requirements.txt
pip install pytest
```

## Architecture

The codebase follows a two-phase pipeline: **Extraction** and **Injection**.

### Public API

The recommended API uses class-based interfaces. Legacy function-based wrappers are available but deprecated.

| Class / Function          | Module                          | Status                  |
| ------------------------- | ------------------------------- | ----------------------- |
| `SVGTranslationExtractor` | `CopySVGTranslation.extraction` | **Current**             |
| `SVGTranslationInjector`  | `CopySVGTranslation.injection`  | **Current**             |
| `ExtractorData`           | `CopySVGTranslation.extraction` | **Current** (dataclass) |
| `InjectorData`            | `CopySVGTranslation.injection`  | **Current** (dataclass) |
| `extract()`               | `CopySVGTranslation.extraction` | Deprecated (wrapper)    |
| `inject()`                | `CopySVGTranslation.injection`  | Deprecated (wrapper)    |

### Core Modules

-   **`CopySVGTranslation/extraction/svg_extractor.py`**: Contains `SVGTranslationExtractor` class and `ExtractorData` dataclass. Parses SVG files and extracts translation pairs from `<switch>` elements. Collects default (English) text and corresponding translations from sibling `<text>` elements with `systemLanguage` attributes.

-   **`CopySVGTranslation/extraction/worker.py`**: Contains the deprecated `extract()` function — a thin wrapper around `SVGTranslationExtractor` for backward compatibility.

-   **`CopySVGTranslation/injection/svg_injector.py`**: Contains `SVGTranslationInjector` class, `InjectorData`, and `InjectorStats` dataclasses. The main injection engine that processes `<switch>` elements, matches default text against mappings, and inserts/updates translation nodes with `systemLanguage` attributes.

-   **`CopySVGTranslation/injection/worker.py`**: Contains the deprecated `inject()` function — a thin wrapper around `SVGTranslationInjector` for backward compatibility.

-   **`CopySVGTranslation/injection/preparation.py`**: SVG normalization and preparation before injection. Wraps loose text nodes in `<tspan>` elements, creates `<switch>` wrappers, normalizes language tags, assigns unique IDs (`trsvg*`), and detects unsupported structures (nested tspans, tref elements).

-   **`CopySVGTranslation/utils/text_utils.py`**: Shared text normalization (trim whitespace, collapse internal whitespace, optional case-insensitivity).

-   **`CopySVGTranslation/titles_workers/`**: Handles title-like text (entries ending with 4-digit years) with special handling.

-   **`CopySVGTranslation/nested_analyze/`**: Utilities for detecting and fixing nested `<tspan>` structures that would otherwise cause `SvgNestedTspanExceptionError`.

### Data Flow

1. **Extraction**: SVG file → `SVGTranslationExtractor.extract()` → `ExtractorData` (with `.to_json()` for dict)

2. **Injection**: SVG file + mapping dict → `SVGTranslationInjector.inject()` → `InjectorData` (with `.new_stats` for stats)

### Key Data Structures

**ExtractorData** (returned by `SVGTranslationExtractor.extract()`):

```python
@dataclass
class ExtractorData:
    new: dict[str, dict[str, str]]     # source text → lang → translation
    tspans_by_id: dict[str, str]       # tspan id → text content
    title: dict[str, Any]              # title-like entries (year stripped)
    title_new: dict[str, Any]          # new-format title translations
    error: str                         # error message or ""
```

**InjectorData** (returned by `SVGTranslationInjector.inject()`):

```python
@dataclass
class InjectorData:
    tree: etree._ElementTree | None    # parsed/modified SVG tree
    new_stats: InjectorStats           # injection statistics
```

**InjectorStats**:

```python
@dataclass
class InjectorStats:
    all_languages: int
    new_languages: int
    processed_switches: int
    inserted_translations: int
    skipped_translations: int
    updated_translations: int
    languages_before: list[str]
    languages_after: list[str]
    error: str
```

### Translation JSON Format

The extractor produces JSON in this format:

```json
{
  "new": {
    "normalized english text": {"ar": "translation", "fr": "translation"}
  },
  "title": {...},
  "tspans_by_id": {"id": "text content"},
  "title_new": {...}
}
```

### Exception Types

-   **`SvgStructureExceptionError`**: Raised for invalid SVG structures (tref elements, CSS with IDs, non-tspan children in text, etc.)
-   **`SvgNestedTspanExceptionError`**: Raised when nested `<tspan>` elements are detected. Use `fix_nested_tspans()` or `fix_nested_file()` to resolve.

## Dependencies

-   **lxml**: XML parsing and manipulation (required)
-   Python 3.10+

## Testing

Tests are organized in `tests/` with subdirectories for extraction, injection, and nested_analyze modules. The `conftest.py` adds the project root to `sys.path`.
