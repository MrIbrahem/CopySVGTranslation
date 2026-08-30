# Titles & Year Handling

The `CopySVGTranslation/titles/` package handles a special class of translatable
text: **titles that contain a 4-digit year**. Examples include chart titles such
as `"COVID-19 pandemic 2020"` or `"Population, 1990"`.

Because the year changes between published versions of a diagram, it is wasteful
to store a separate translation for every year. Instead, CopySVGTranslation can
canonicalize these titles into a single `{year}` template and reuse the
translations across years.

## Why year-aware titles exist

Wikimedia Commons diagrams are frequently re-published with updated data (new
year, same wording). Without year handling, a title like
`"COVID-19 pandemic 2020"` would need a completely separate translation from
`"COVID-19 pandemic 2021"`, even though only the year differs. Year templates let
one set of translations cover every year variant.

## The `enable_year_titles` flag

Year handling is gated by `config.enable_year_titles` (the
`YearTitleHandler.enabled` property). When disabled, no title templating happens
and titles are treated like any other text.

```python
from CopySVGTranslation import SVGTranslationService, TranslationConfig

service = SVGTranslationService(
    TranslationConfig(enable_year_titles=True)
)
```

## Extraction: building templates

On extraction, `YearTitleHandler.build_templates()` scans `mapping.new` and, for
every source whose translations all end in the same 4-digit year, produces an
entry in `mapping.title_new` with the year replaced by `{year}`.

Input (`mapping.new`):

```python
{
    "COVID-19 pandemic 2020": {
        "ar": "جائحة كوفيد 2020",
        "es": "Pandemia de COVID-19 2020",
    }
}
```

Output (`mapping.title_new`):

```python
{
    "COVID-19 pandemic {year}": {
        "ar": "جائحة كوفيد {year}",
        "es": "Pandemia de COVID-19 {year}",
    }
}
```

### `create_lang_template`

`config.create_lang_template` controls template generation for languages where
the translation does not literally end in the year. When enabled,
`build_lang_template()` derives a template such as `"{value}, {year}"` so that a
translation like `"Prevalència de la malaltia de Parkinson"` (Catalan, no year
suffix) can still be matched and expanded.

`process_header_titles()` additionally pulls year-bearing titles out of
`mapping.meta["header"]`, templates them, strips the year, and merges the
year-free translations back into `mapping.new` — so header titles participate in
normal translation without duplicating work.

## Injection: expanding templates

On injection, `expand_for_texts()` does the reverse. Given the fallback
(default) texts of a switch, it finds matching year templates in
`title_new`, substitutes the concrete year, and returns extra translation entries
to merge into the working map.

```python
mapping.title_new = {
    "COVID-19 pandemic {year}": {"ar": "جائحة كوفيد {year}"}
}
default_texts = ["COVID-19 pandemic 1990"]

# expanded ->
{
    "COVID-19 pandemic 1990": {"ar": "جائحة كوفيد 1990"}
}
```

`enrich_mapping_for_switch()` wraps this into a fresh working `TranslationMapping`
(which the injector then uses) without mutating the original mapping. This is what
lets a `{year}` template contribute translations for a specific year at injection
time even when that exact year was never present in the source mapping.

## Key helpers

| Helper                                      | Direction | Purpose                                                   |
| ------------------------------------------- | --------- | --------------------------------------------------------- |
| `match_year(text)`                          | —         | Extract a 4-digit year from the start or end of a string. |
| `replace_year_with_placeholder(text, year)` | extract   | Turn `"... 2020"` into `"... {year}"`.                    |
| `apply_year(template, year)`                | inject    | Turn `"... {year}"` into `"... 2020"`.                    |
| `build_templates(mapping)`                  | extract   | Populate `mapping.title_new` from `mapping.new`.          |
| `expand_for_texts(mapping, default_texts)`  | inject    | Expand `{year}` templates for concrete fallback texts.    |

## Data model relationship

Year templates live in `TranslationMapping.title_new` (see
[data-models.md](data-models.md)). They are consumed during injection and are
the reason `TranslationMapping` carries `title_new` separately from `new`.
