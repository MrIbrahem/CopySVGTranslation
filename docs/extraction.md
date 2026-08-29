# Extraction

Extraction reads a multilingual SVG and produces a `TranslationMapping` (see
[data-models.md](data-models.md)). The high-level entry point is
`SVGTranslationService.extract()`; the engine is `SVGTranslationExtractor`.

## What gets extracted

The extractor walks every `<switch>` in the document. For each switch it:

1. Locates the **fallback** `<text>` (the node without `systemLanguage`).
2. Reads the default text segments (the `<tspan>`/text contents).
3. Records each language node (`systemLanguage="XX"`) as a `{lang: translation}`
   entry keyed by the normalized default source text.

```xml
<switch>
  <text id="t0-ar" systemLanguage="ar">مرحبا</text>
  <text id="t0-fr" systemLanguage="fr">Bonjour</text>
  <text id="t0">Hello</text>
</switch>
```

becomes (in `mapping.new`):

```json
{ "hello": { "ar": "مرحبا", "fr": "Bonjour" } }
```

Source keys are lowercased when `case_insensitive=True` (the default), matching
how injection looks them up.

## Using the service

```python
from CopySVGTranslation import SVGTranslationService

service = SVGTranslationService()
result = service.extract("source.svg", save_mapping=True)

if result.success:
    mapping = result.data
    print(mapping.to_json())
```

### Saving the mapping

`save_mapping` accepts:

-   `None` / `False` — do not save.
-   `True` — save to `<mapping_output_dir>/<name>.json` (or the conventional
    `<parent>/data/<name>.json` when `mapping_output_dir` is unset).
-   a `Path`/`str` — save to that explicit file.

If extraction succeeds but the mapping cannot be saved, `success` stays `True` and
the problem is reported in `result.warnings`.

## Prepare-before-extract

Some SVGs are not in the "one `<switch>` per translatable text" shape this library
expects. Set `TranslationConfig.prepare_before_extraction=True` to run the
preparation pipeline (see [preparation.md](preparation.md)) _in memory_ before
extraction. The file on disk is not modified.

```python
from CopySVGTranslation import SVGTranslationService, TranslationConfig

service = SVGTranslationService(TranslationConfig(prepare_before_extraction=True))
result = service.extract("unprepared.svg")
```

## Year-aware titles

When `enable_year_titles=True` (default), the extractor additionally builds
`title_new` templates: a source like `"music in 2020"` becomes a template
`"music in {year}"` with `{year}` placeholders in each language. This lets
injection re-expand the title for different years. The feature is transparent for
normal translation copy — you can ignore `title_new` unless you need it.

## Headers

Header-specific text (parsed from the document) is stored under `mapping.meta["header"]`
and, when `create_lang_template=True`, expanded into `mapping.new` so the same
translations are available during injection.

## Errors

`extract()` returns `OperationResult.fail(...)` (not an exception) in these cases:

-   File not found → `error_code` derived from `SvgIOError`.
-   Unparseable XML → derived from `SvgParseError`.
-   No translations found → `error_code="no_translations"`.

Always check `result.success` before using `result.data`.
