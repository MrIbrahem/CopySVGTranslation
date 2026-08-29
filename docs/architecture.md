# Architecture

This document explains how CopySVGTranslation is organized and how data flows
through it. It is the starting point for understanding the codebase.

## What the library does

CopySVGTranslation works with **multilingual SVG files**: SVGs that use
`<switch>` elements containing one `<text>` node per language, each tagged with a
`systemLanguage` attribute. A single fallback `<text>` (no `systemLanguage`) holds
the default language.

```xml
<svg xmlns="http://www.w3.org/2000/svg">
  <switch>
    <text id="t0-ar" systemLanguage="ar">مرحبا</text>
    <text id="t0-fr" systemLanguage="fr">Bonjour</text>
    <text id="t0">Hello</text>          <!-- fallback, must be LAST -->
  </switch>
</svg>
```

The library can:

-   **Extract** the existing translations from such a file into a `TranslationMapping`.
-   **Inject** a `TranslationMapping` (or a compatible dict) into another SVG,
    inserting or updating `<text systemLanguage="XX">` nodes.
-   **Prepare** an arbitrary SVG so its structure conforms to what extraction and
    injection expect.
-   **Repair** nested `<tspan>` / `<a>` structures.
-   **Check and fix** switch ordering so files render correctly on Wikimedia Commons.

## Layered design

The library follows a **facade + pipeline** design. The only supported public
entry point is `SVGTranslationService` (in `CopySVGTranslation/service.py`),
backed by `TranslationConfig` and `TranslationMapping`. All other classes
(extractor, injector, preparer, etc.) are internal collaborators created by the
service.

```
                 SVGTranslationService   (facade — the public API)
                 /        |        \          \            \
        Extractor   Injector   SwitchOrderChecker   NestedStructureService
                            |                              |
                    SvgPreparationPipeline          Nested detector / flattener
                            |
                  PreparationStep chain
                            |
                  utils.xml / utils.text / io / titles
```

## Module map

| Module                                       | Responsibility                                                                          |
| -------------------------------------------- | --------------------------------------------------------------------------------------- |
| `CopySVGTranslation/service.py`              | `SVGTranslationService` facade. The public API.                                         |
| `CopySVGTranslation/config.py`               | `TranslationConfig` dataclass — all tunable behavior.                                   |
| `CopySVGTranslation/core/`                   | Data models: `TranslationMapping`, `TranslationEntry`, `InjectorData`, `InjectorStats`. |
| `CopySVGTranslation/extraction/`             | `SVGTranslationExtractor` — reads SVGs into a `TranslationMapping`.                     |
| `CopySVGTranslation/injection/`              | `SVGTranslationInjector`, `SwitchProcessor`, `TranslationApplier`, `IdManager`.         |
| `CopySVGTranslation/preparation/`            | `SvgPreparationPipeline` and its ordered `PreparationStep`s.                            |
| `CopySVGTranslation/nested/`                 | Detect and flatten/repair nested `<tspan>`/`<a>` structures.                            |
| `CopySVGTranslation/titles/`                 | Year-aware title handling (`YearTitleHandler`).                                         |
| `CopySVGTranslation/io/`                     | SVG loading/writing (`SvgDocument`), mapping JSON I/O (`MappingStore`), output paths.   |
| `CopySVGTranslation/result.py`               | `OperationResult` — uniform return type for every service method.                       |
| `CopySVGTranslation/switch_order_checker.py` | `SwitchOrderChecker` — read-only ordering check + fix.                                  |
| `CopySVGTranslation/utils/`                  | `xml.py` (XML helpers, switch sorting) and `text.py` (text/lang normalization).         |

## Data flow

```
Extraction:
    SVG file ──▶ SVGTranslationExtractor.extract() ──▶ TranslationMapping

Injection:
    SVG file + TranslationMapping ──▶ SVGTranslationInjector.inject()
                                       ├─ SvgPreparationPipeline.run()   (normalize)
                                       ├─ SwitchProcessor per <switch>   (match + apply)
                                       └─ _finalize_switches()          (reorder, stats)
                                    ──▶ InjectorData (tree + InjectorStats)

Service facade:
    Every public method returns OperationResult[Payload] regardless of success.
```

## Why the facade?

Two design choices keep the surface area small and stable:

1. **One entry point.** Callers depend only on `SVGTranslationService`. Internal
   components can change freely as long as the service's method signatures stay
   the same.
2. **Uniform results.** Every service method returns an `OperationResult`, so
   callers check `success` once and then consume `data` / `stats`, or inspect
   `error` / `error_code` / `warnings`. There is no mix of exceptions and
   return-value checks across the public API (internal helpers may still raise).

## Commons rendering constraint

On `commons.wikimedia.org`, a `<switch>` only renders its non-default children
when the fallback `<text>` (the one without `systemLanguage`) is the **last**
child. CopySVGTranslation enforces this invariant in two places:

-   During injection, `SwitchProcessor` reorders each switch with the fallback
    last (default config `sort_switches=True`).
-   Independently, `SwitchOrderChecker` / `service.check_switches_sorted()` let you
    verify a _file you did not produce with this library_ before re-uploading it.

See [switch-ordering.md](switch-ordering.md) for details, and
[preparation.md](preparation.md) for the reorder step.
