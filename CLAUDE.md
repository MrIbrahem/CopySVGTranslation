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

### Core Modules

- **`CopySVGTranslation/extraction/extractor.py`**: Parses SVG files and extracts translation pairs from `<switch>` elements. Collects default (English) text and corresponding translations from sibling `<text>` elements with `systemLanguage` attributes.

- **`CopySVGTranslation/injection/injector.py`**: The main injection engine. Processes `<switch>` elements, matches default text against mappings, and inserts/updates translation nodes with `systemLanguage` attributes.

- **`CopySVGTranslation/injection/preparation.py`**: SVG normalization and preparation before injection. Wraps loose text nodes in `<tspan>` elements, creates `<switch>` wrappers, normalizes language tags, assigns unique IDs (`trsvg*`), and detects unsupported structures (nested tspans, tref elements).

- **`CopySVGTranslation/injection/batch.py`**: Batch processing utilities (`start_injects`) for applying translations to multiple files.

- **`CopySVGTranslation/workflows.py`**: High-level convenience functions (`svg_extract_and_inject`, `svg_extract_and_injects`) that combine extraction and injection in one call.

- **`CopySVGTranslation/text_utils.py`**: Shared text normalization (trim whitespace, collapse internal whitespace, optional case-insensitivity).

- **`CopySVGTranslation/titles.py`**: Handles title-like text (entries ending with 4-digit years) with special handling.

- **`CopySVGTranslation/nested_analyze/`**: Utilities for detecting and fixing nested `<tspan>` structures that would otherwise cause `SvgNestedTspanExceptionError`.

### Data Flow

1. **Extraction**: SVG file -> `extract()` -> JSON mapping (`{"new": {"english text": {"ar": "...", "fr": "..."}}}`)

2. **Injection**: SVG file + JSON mapping -> `inject()` -> Modified SVG with new `<text systemLanguage="XX">` nodes

3. **Full workflow**: `svg_extract_and_inject()` extracts from source SVG and injects into target SVG in one step.

### Key Data Structure

The translation JSON format:
```json
{
  "new": {
    "normalized english text": {"ar": "translation", "fr": "translation"}
  },
  "title": {...},
  "tspans_by_id": {"id": "text content"}
}
```

### Exception Types

- **`SvgStructureExceptionError`**: Raised for invalid SVG structures (tref elements, CSS with IDs, non-tspan children in text, etc.)
- **`SvgNestedTspanExceptionError`**: Raised when nested `<tspan>` elements are detected. Use `fix_nested_tspans()` or `fix_nested_file()` to resolve.

## Dependencies

- **lxml**: XML parsing and manipulation (required)
- **tqdm**: Progress bars for batch operations (optional)
- Python 3.10+

## Testing

Tests are organized in `tests/` with subdirectories for extraction, injection, and nested_analyze modules. The `conftest.py` adds the project root to `sys.path`.
