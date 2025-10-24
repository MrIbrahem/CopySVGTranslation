# SVG Translation Tool

This tool extracts multilingual text pairs from SVG files and applies translations to other SVG files by inserting missing `<text systemLanguage="XX">` blocks.

## Installation

This tool requires Python 3.10+. Install the lightweight core dependencies with:

```bash
pip install CopySvgTranslate
```
## Usage

### Extracting and injecting in a single step

```python
from pathlib import Path
from CopySvgTranslate import svg_extract_and_inject

tree = svg_extract_and_inject(
    extract_file=Path("examples/source_multilingual.svg"),
    inject_file=Path("examples/target_missing_translations.svg"),
    data_output_file = Path("examples/data.json")
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
from CopySvgTranslate.injection import inject

tree, stats = inject(
    inject_file="examples/target_missing_translations.svg",
    mapping_files=["CopySvgTranslate/data/source_multilingual.svg.json"],
    output_dir=Path("./translated"),
    save_result=True,
    return_stats=True,
)

print(stats)
```

### Injecting with pre-translated data

When you already have the translation JSON, load it and use
`svg_extract_and_injects` directly. Important parameters include `overwrite`
to update existing translations and `output_dir` to control where translated
files are written.

```python
from pathlib import Path
from CopySvgTranslate import svg_extract_and_injects

translations = {
    "new": {
        "Hello": {"ar": "مرحبًا", "fr": "Bonjour"},
    }
}

tree, stats = svg_extract_and_injects(
    translations=translations,
    inject_file=Path("examples/target_missing_translations.svg"),
    save_result=True,
    overwrite=True,
    output_dir=Path("./translated"),
    return_stats=True,
)

print("Saved to", Path("./translated/target_missing_translations.svg"))
print(stats)
```

## Data Model

The extractor writes a JSON document rooted under the `"new"` key. Each entry
maps normalized English text to a dictionary of language codes and
translations. Metadata such as `"default_tspans_by_id"` is used internally to
reconstruct the SVG structure during injection. An example of the modern
format:

```json
{
  "new": {
    "default_tspans_by_id": {
      "text2213": "but are connected in anti-phase"
    },
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
<switch style="font-size:30px;font-family:Bitstream Vera Sans">
    <text x="259.34814" y="927.29651" style="font-size:30px;font-family:Bitstream Vera Sans"
        id="text2213-ar"
        xml:space="preserve" systemLanguage="ar">
        <tspan x="259.34814" y="927.29651" id="tspan2215-ar">لكنها موصولة بمرحلتين متعاكستين.</tspan>
    </text>
    <text x="259.34814" y="927.29651" style="font-size:30px;font-family:Bitstream Vera Sans"
        id="text2213"
        xml:space="preserve">
        <tspan x="259.34814" y="927.29651" id="tspan2215">but are connected in anti-phase</tspan>
    </text>
</switch>
```

### Extracted JSON (arabic.svg.json)

```json
{
  "new": {
    "default_tspans_by_id": {
      "text2213": "but are connected in anti-phase"
    },
    "but are connected in anti-phase": {
      "ar": "لكنها موصولة بمرحلتين متعاكستين."
    }
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
