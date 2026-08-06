# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CopySVGTranslation is a Python library for extracting multilingual text pairs from SVG files and applying translations by inserting `<text systemLanguage="XX">` blocks. It works with SVG files that use `<switch>` elements containing `<text>` nodes with `systemLanguage` attributes.

## Commands

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run a specific test file
poetry run pytest tests/unit/extraction/test_extractor.py -v
```

### Installation for Development

```bash
poetry install
# or
poetry run pip install -r requirements.txt -r dev-requirements.txt
```

## Architecture

The codebase follows a modular pipeline: **Preparation**, **Extraction**, **Injection**, and a unified **Service Facade**.

### Public API

The primary, recommended API uses class-based interfaces. Legacy function-based wrappers are available but deprecated.

| Class / Function          | Module                          | Status                  |
| ------------------------- | ------------------------------- | ----------------------- |
| `SVGTranslationService`   | `CopySVGTranslation.service`    | **Current** (Facade)    |
| `SVGTranslationExtractor` | `CopySVGTranslation.extraction` | **Current**             |
| `SVGTranslationInjector`  | `CopySVGTranslation.injection`  | **Current**             |
| `TranslationMapping`      | `CopySVGTranslation.core`       | **Current** (dataclass) |
| `InjectorData`            | `CopySVGTranslation.injection`  | **Current** (dataclass) |
| `extract()`               | `CopySVGTranslation.legacy`     | Deprecated (wrapper)    |
| `inject_file_tree()`      | `CopySVGTranslation.legacy`     | Deprecated (wrapper)    |

### Core Modules

-   **`CopySVGTranslation/service.py`**: The main high-level facade (`SVGTranslationService`). Orchestrates extraction, injection, file load/saves, and result mapping.
-   **`CopySVGTranslation/extraction/extractor.py`**: Contains `SVGTranslationExtractor` class. Parses SVG files and extracts translation pairs from `<switch>` elements into a `TranslationMapping`.
-   **`CopySVGTranslation/injection/injector.py`**: Contains `SVGTranslationInjector` class. The main injection engine that coordinates the preparation of SVGs and delegation to the switch processor.
-   **`CopySVGTranslation/injection/switch_processor.py`**: Processes every `<switch>` element, matching source text and adding/updating translations.
-   **`CopySVGTranslation/injection/translation_applier.py`**: Inserts or updates translation nodes with `systemLanguage` attributes.
-   **`CopySVGTranslation/injection/id_manager.py`**: Tracks ID registration and allocations dynamically to prevent collision.
-   **`CopySVGTranslation/preparation/preparer.py`**: Organizes sequential `PreparationStep` rules (such as wrapping texts inside `<switch>` nodes and normalizing language tags).
-   **`CopySVGTranslation/nested/`**: Utilities for detecting and fixing nested `<tspan>` structures.
-   **`CopySVGTranslation/titles/year_handler.py`**: Handles title-like text (entries containing a 4-digit year) with specialized expansion logic.
-   **`CopySVGTranslation/utils/text.py`**: Shared text and language code normalization functions.
-   **`CopySVGTranslation/utils/xml.py`**: XML manipulation helpers.

### Data Flow

1. **Extraction**: SVG file → `SVGTranslationExtractor.extract()` → `TranslationMapping`
2. **Injection**: SVG file + `TranslationMapping` → `SVGTranslationInjector.inject()` → `InjectorData` (containing stats)

### Key Data Structures

**TranslationMapping** (returned by extractor):

```python
@dataclass
class TranslationMapping:
    new: dict[str, dict[str, str]]     # source text → lang → translation
    tspans_by_id: dict[str, str]       # tspan id → text content
    title_new: dict[str, Any]          # new-format title translations
    meta: dict[str, Any]               # metadata and diagnostics
```

**InjectorData** (returned by injector):

```python
@dataclass
class InjectorData:
    tree: etree._ElementTree | None    # parsed/modified SVG tree
    inject_stats: InjectorStats        # injection statistics
```

### Exception Types

-   **`CopySVGTranslationError`**: System base error.
-   **`SvgStructureError`**: Raised for invalid SVG structures.
-   **`SvgNestedTspanError`**: Raised when nested `<tspan>` elements are found.

## Dependencies

-   **lxml**: XML parsing and manipulation
-   Python 3.10+
