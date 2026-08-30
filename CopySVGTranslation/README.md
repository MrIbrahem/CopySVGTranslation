# copy_svg_translation

Main package for SVG copy and translation workflows (v2.1).

## Project Structure

```
CopySVGTranslation/
├── __init__.py              ├── config.py                # TranslationConfig (central settings)
├── service.py               # SVGTranslationService (facade)
├── result.py                # OperationResult (uniform return type)
├── exceptions.py            # Exception hierarchy with i18n codes
├── core/
│   ├── mapping.py           # TranslationMapping, InjectorStats
│   ├── models.py            # NestedStrategy enum, type aliases
│   ├── switch_node.py       # SwitchNode wrapper for <switch> elements
│   └── text_node.py         # TextNode wrapper for <text> elements
├── extraction/
│   ├── extractor.py         # SVGTranslationExtractor
│   └── strategies.py        # ByTspanId, ByPosition, Composite strategies
├── injection/
│   ├── injector.py          # SVGTranslationInjector (main engine)
│   ├── switch_processor.py  # Per-<switch> processing logic
│   ├── translation_applier.py # Node insertion/update logic
│   └── id_manager.py        # Dynamic ID registration & allocation
├── preparation/
│   ├── preparer.py          # SvgPreparationPipeline (step runner)
│   └── steps/               # Individual PreparationStep classes
├── nested/
│   ├── service.py           # NestedStructureService
│   ├── detector.py          # NestedTspanDetector
│   ├── flattener.py         # NestedTspanFlattener (repair)
│   └── objects.py           # RepairResult data class
├── titles/
│   ├── year_handler.py      # YearTitleHandler (year-aware titles)
│   └── year_stripper.py     # Year stripping utilities
├── io/
│   ├── mapping_store.py     # JSON mapping load/save/merge
│   ├── svg_document.py      # SvgDocument I/O holder
│   ├── svg_writer.py        # SVG serialization to disk
│   └── output_paths.py      # Output path resolution logic
└── utils/
    ├── text.py              # Text & language-code normalization
    └── xml.py               # XML manipulation helpers
```

## Packages

| Package       | Description                               | Documentation                                        |
| ------------- | ----------------------------------------- | ---------------------------------------------------- |
| `core`        | Core models, mapping, and node handling   | [data-models.md](../docs/data-models.md)             |
| `extraction`  | Content extraction strategies             | [extraction.md](../docs/extraction.md)               |
| `injection`   | Translation injection pipeline            | [injection.md](../docs/injection.md)                 |
| `preparation` | pre injection steps                       | [preparation.md](../docs/preparation.md)             |
| `io`          | SVG document and mapping I/O              | [architecture.md](../docs/architecture.md)           |
| `nested`      | Nested structure detection and flattening | [nested-structures.md](../docs/nested-structures.md) |
| `titles`      | Title and year handling                   | [titles.md](../docs/titles.md)                       |
| `utils`       | Shared text and XML utilities             | [architecture.md](../docs/architecture.md)           |

## Additional documentation

-   [Architecture & data flow](../docs/architecture.md)
-   [Getting started](../docs/getting-started.md)
-   [Exceptions & operation results](../docs/data-models.md)
-   [Documentation index](../docs/README.md)
