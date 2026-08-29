# Documentation Index

This folder holds the long-form documentation for CopySVGTranslation. The `README.md`
at the repository root is the user-facing quick start; these pages cover each
subsystem in depth.

## Start here

-   [getting-started.md](getting-started.md) — install, the public API, and a
    five-minute tour of the common workflows.
-   [architecture.md](architecture.md) — layered facade + pipeline design, the module
    map, and the Wikimedia Commons rendering constraint.

## Core concepts

-   [data-models.md](data-models.md) — `TranslationMapping`, `TranslationEntry`,
    `InjectorData`, `InjectorStats`, `Error`, and `OperationResult`.

## Pipelines

-   [extraction.md](extraction.md) — reading translations out of an SVG.
-   [injection.md](injection.md) — applying a mapping to an SVG.
-   [preparation.md](preparation.md) — the ordered `PreparationStep` pipeline that
    normalizes an arbitrary SVG.

## Maintenance operations

-   [nested-structures.md](nested-structures.md) — detecting and repairing nested
    `<tspan>` / `<a>` structures.
-   [switch-ordering.md](switch-ordering.md) — checking and fixing `<switch>` ordering
    before re-uploading to Commons.

## How the modules map to these docs

| Package                                      | Primary doc                                                                  |
| -------------------------------------------- | ---------------------------------------------------------------------------- |
| `CopySVGTranslation/service.py`              | [architecture.md](architecture.md), [getting-started.md](getting-started.md) |
| `CopySVGTranslation/extraction/`             | [extraction.md](extraction.md)                                               |
| `CopySVGTranslation/injection/`              | [injection.md](injection.md)                                                 |
| `CopySVGTranslation/preparation/`            | [preparation.md](preparation.md)                                             |
| `CopySVGTranslation/nested/`                 | [nested-structures.md](nested-structures.md)                                 |
| `CopySVGTranslation/switch_order_checker.py` | [switch-ordering.md](switch-ordering.md)                                     |
| `CopySVGTranslation/core/`                   | [data-models.md](data-models.md)                                             |
