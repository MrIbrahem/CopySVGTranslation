# SVG Translation Tool

This tool extracts multilingual text pairs from SVG files and applies translations to other SVG files by inserting missing `<text systemLanguage="XX">` blocks.

## Installation

This tool requires Python 3.10+. Install the lightweight core dependencies with:

```bash
pip install CopySVGTranslation
```
## Usage

### Extracting and injecting in a single step

```python
from pathlib import Path
from CopySVGTranslation import svg_extract_and_inject

tree = svg_extract_and_inject(
    extract_file=Path("examples/source_multilingual.svg"),
    inject_file=Path("examples/target_missing_translations.svg"),
    data_output_file = Path("examples/data.json"),
    save_result=True,
)

if tree is not None:
    print("Injection completed!")
```

The helper stores the extracted phrases under `Path("examples/data.json")` and,
when `save_result=True`, writes the translated SVG to
`output_dir=Path("./translated")`. If you also need statistics about how many
translations were inserted, call the lower level injector with
`return_stats=True`:

```python
from CopySVGTranslation.injection import inject

tree, stats = inject(
    inject_file="examples/target_missing_translations.svg",
    mapping_files=["CopySVGTranslation/data/source_multilingual.svg.json"],
    output_dir=Path("./translated"),
    save_result=True,
    return_stats=True,
)

print(stats)
```

### Injecting with pre-translated data

When you already have the translation JSON, load it and use
`inject` directly. Important parameters include `overwrite`
to update existing translations and `output_dir` to control where translated
files are written.

```python
from pathlib import Path
from CopySVGTranslation import inject

translations = {
    "new": {
        "Hello": {"ar": "مرحبًا", "fr": "Bonjour"},
    }
}

tree, stats = inject(
    inject_file=Path("examples/target_missing_translations.svg"),
    all_mappings=translations,
    output_dir=Path("./translated"),
    overwrite=True,
    save_result=True,
    return_stats=True,
)

print("Saved to", Path("./translated/target_missing_translations.svg"))
print(stats)
```

## Data Model

The extractor writes a JSON document rooted under the `"new"` key. Each entry
maps normalized English text to a dictionary of language codes and translations.
An example of the modern format:

```json
{
  "new": {
    "but are connected in anti-phase": {
      "ar": "لكنها موصولة بمرحلتين متعاكستين."
    }
  }
}
```

Older exports may omit the wrapper and look like
`{"english": {"ar": "…"}}`. The injector transparently accepts both
structures, but the recommended format is the nested `"new"` layout shown
above.

## Extract Example

### Input SVG (arabic.svg)

```xml
<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <switch>
      <text id="t0-ar" systemLanguage="ar">
          <tspan id="t0-ar">الموسيقى في عام 2020</tspan>
      </text>
      <text id="t0-fr" systemLanguage="fr">
          <tspan id="t0-fr">La musique en 2020</tspan>
      </text>
      <text id="t0">
          <tspan id="t0">Music in 2020</tspan>
      </text>
  </switch>
  <switch>
      <text id="t0-ar" systemLanguage="ar">
          <tspan id="t0-ar">مرحبا</tspan>
      </text>
      <text id="t0-fr" systemLanguage="fr">
          <tspan id="t0-fr">Bonjour</tspan>
      </text>
      <text id="t0">
          <tspan id="t0">Hello</tspan>
      </text>
  </switch>
</svg>
```

### Python code

```python
from pathlib import Path
from CopySVGTranslation import extract

translations = extract(
    svg_file_path=Path("arabic.svg"),
    case_insensitive=True,
)
```
### Extracted JSON

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
    "title": {
        "music in": {
            "ar": "الموسيقى في عام",
            "fr": "La musique en"
        }
    },
    "tspans_by_id": {
        "t0": "Hello"
    }
}
```


### Injection Example
- TODO

## Testing

Run the unit tests:

```bash
python -m pytest tests -v
```

## Implementation Details

### Text Normalization

The tool normalizes text by:
- Trimming leading and trailing whitespace
- Replacing multiple internal whitespace characters with a single space
- Optionally converting to lowercase for case-insensitive matching

### ID Generation

When adding new translation nodes, the tool generates unique IDs by:
- Taking the existing ID and appending the language code (e.g., `text2213` becomes `text2213-ar`)
- If the generated ID already exists, appending a numeric suffix until unique (e.g., `text2213-ar-1`)

## Error Handling

The tool includes comprehensive error handling for:
- Missing input files
- Invalid XML structure
- Missing required attributes
- File permission issues
