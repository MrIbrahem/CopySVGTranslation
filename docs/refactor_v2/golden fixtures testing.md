# Golden Fixture Testing

Practical setup for regression-testing the `preparation`, `nested`, and `extraction` refactors without changing behaviour.

---

## 1. What “golden fixtures” means here

| Piece | Role |
|-------|------|
| **Input SVG** | Fixed sample under `tests/fixtures/…` |
| **Golden artifact** | Expected output (normalized SVG XML or extract JSON) |
| **Test** | Run pipeline/extractor → compare to golden (stable normalization) |

If the refactor is behaviour-preserving, tests must pass unchanged before and after.

---

## 2. Layout

```text
tests/
  fixtures/
    svg/
      simple_switch.svg
      multi_lang_comma.svg
      nested_tspan_style.svg
      empty_nodes.svg
      missing_ids.svg
      header_subtitle.svg
      invalid_dup_lang.svg          # expects specific error
    golden/
      extract/
        simple_switch.json
        header_subtitle.json
      prepared/
        simple_switch.svg
        nested_tspan_style__preserve_style.svg
        empty_nodes.svg
  test_preparation_golden.py
  test_extraction_golden.py
  test_nested_golden.py
  conftest.py
  _normalize.py
```

---

## 3. Normalization helpers

Comparisons must ignore irrelevant churn (attribute order, trivial whitespace).

```python
# tests/_normalize.py
from __future__ import annotations

import json
import re
from lxml import etree


def normalize_svg_bytes(data: bytes | str) -> str:
    """Parse and re-serialize for stable comparison."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(data, parser=parser)
    # Optional: sort attributes for stability
    for el in root.iter():
        if el.attrib:
            items = sorted(el.attrib.items())
            el.attrib.clear()
            el.attrib.update(items)
    return etree.tostring(
        root,
        encoding="unicode",
        pretty_print=True,
    )


def normalize_mapping_dict(d: dict) -> str:
    """Stable JSON for TranslationMapping.to_json()."""
    def _sort(obj):
        if isinstance(obj, dict):
            return {k: _sort(obj[k]) for k in sorted(obj)}
        if isinstance(obj, list):
            return [_sort(x) for x in obj]
        return obj

    return json.dumps(_sort(d), ensure_ascii=False, indent=2) + "\n"
```

---

## 4. `conftest.py`

```python
# tests/conftest.py
from __future__ import annotations

from pathlib import Path
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def svg_dir(fixtures_dir: Path) -> Path:
    return fixtures_dir / "svg"


@pytest.fixture
def golden_dir(fixtures_dir: Path) -> Path:
    return fixtures_dir / "golden"
```

---

## 5. Preparation golden tests

```python
# tests/test_preparation_golden.py
from __future__ import annotations

from pathlib import Path
import pytest
from lxml import etree

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.preparation import SvgPreparationPipeline
from tests._normalize import normalize_svg_bytes


def _prepare(svg_path: Path, **cfg_overrides) -> bytes:
    config = TranslationConfig(**cfg_overrides)
    pipeline = SvgPreparationPipeline(config)
    tree, _ = pipeline.run(svg_path)
    return etree.tostring(tree.getroot(), encoding="utf-8", pretty_print=True)


@pytest.mark.parametrize(
    "name,overrides",
    [
        ("simple_switch", {}),
        ("empty_nodes", {}),
        ("missing_ids", {"assign_missing_ids": True}),
        ("nested_tspan_style", {"nested_strategy": "preserve_style"}),
        ("multi_lang_comma", {}),
    ],
)
def test_prepare_matches_golden(svg_dir, golden_dir, name, overrides):
    src = svg_dir / f"{name}.svg"
    golden_path = golden_dir / "prepared" / f"{name}.svg"
    if name == "nested_tspan_style":
        golden_path = golden_dir / "prepared" / f"{name}__preserve_style.svg"

    actual = normalize_svg_bytes(_prepare(src, **overrides))
    expected = normalize_svg_bytes(golden_path.read_bytes())
    assert actual == expected


def test_dup_lang_raises(svg_dir):
    from CopySVGTranslation.exceptions import SvgStructureError

    config = TranslationConfig()
    pipeline = SvgPreparationPipeline(config)
    with pytest.raises(SvgStructureError) as exc:
        pipeline.run(svg_dir / "invalid_dup_lang.svg")
    assert "multiple-text-same-lang" in str(exc.value) or (
        getattr(exc.value, "code", "") == "structure-error-multiple-text-same-lang"
    )
```

---

## 6. Extraction golden tests

```python
# tests/test_extraction_golden.py
from __future__ import annotations

from pathlib import Path
import pytest

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.extraction import SVGTranslationExtractor
from tests._normalize import normalize_mapping_dict


@pytest.mark.parametrize("name", ["simple_switch", "header_subtitle"])
def test_extract_matches_golden(svg_dir, golden_dir, name):
    config = TranslationConfig(case_insensitive=True, enable_year_titles=True)
    extractor = SVGTranslationExtractor(config)
    mapping = extractor.extract(svg_dir / f"{name}.svg")

    actual = normalize_mapping_dict(mapping.to_json())
    expected = normalize_mapping_dict(
        __import__("json").loads((golden_dir / "extract" / f"{name}.json").read_text())
    )
    assert actual == expected
```

---

## 7. Nested (strategy) golden tests

Prefer testing via preparation (real path). Optional direct flattener checks:

```python
# tests/test_nested_golden.py
from __future__ import annotations

from pathlib import Path
import pytest
from lxml import etree

from CopySVGTranslation.nested import NestedTspanFlattener, NestedTspanDetector
from tests._normalize import normalize_svg_bytes


@pytest.mark.parametrize("strategy", ["flatten", "preserve_style"])
def test_flattener_strategy(svg_dir, golden_dir, strategy):
    src = svg_dir / "nested_tspan_style.svg"
    tree = etree.parse(str(src))
    root = tree.getroot()

    NestedTspanFlattener(strategy=strategy).process(root)
    actual = normalize_svg_bytes(etree.tostring(root, encoding="utf-8"))

    golden = golden_dir / "prepared" / f"nested_tspan_style__{strategy}.svg"
    expected = normalize_svg_bytes(golden.read_bytes())
    assert actual == expected


def test_detector_finds_nested(svg_dir):
    tree = etree.parse(str(svg_dir / "nested_tspan_style.svg"))
    found = NestedTspanDetector().find_in_tree(tree.getroot())
    assert len(found) >= 1
```

---

## 8. How to generate / update goldens

One-shot script (dev only):

```python
# tests/scripts/update_goldens.py
"""Regenerate golden files. Run only when behaviour change is intentional."""
from pathlib import Path
from lxml import etree
import json

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.preparation import SvgPreparationPipeline
from CopySVGTranslation.extraction import SVGTranslationExtractor
from tests._normalize import normalize_svg_bytes, normalize_mapping_dict

ROOT = Path(__file__).resolve().parents[1] / "fixtures"
SVG = ROOT / "svg"
OUT_PREP = ROOT / "golden" / "prepared"
OUT_EXT = ROOT / "golden" / "extract"
OUT_PREP.mkdir(parents=True, exist_ok=True)
OUT_EXT.mkdir(parents=True, exist_ok=True)


def dump_prepared(name: str, **overrides):
    cfg = TranslationConfig(**overrides)
    tree, _ = SvgPreparationPipeline(cfg).run(SVG / f"{name}.svg")
    data = etree.tostring(tree.getroot(), encoding="utf-8", pretty_print=True)
    suffix = ""
    if "nested_strategy" in overrides:
        suffix = f"__{overrides['nested_strategy']}"
    path = OUT_PREP / f"{name}{suffix}.svg"
    path.write_text(normalize_svg_bytes(data), encoding="utf-8")
    print("wrote", path)


def dump_extract(name: str):
    m = SVGTranslationExtractor(TranslationConfig()).extract(SVG / f"{name}.svg")
    path = OUT_EXT / f"{name}.json"
    path.write_text(normalize_mapping_dict(m.to_json()), encoding="utf-8")
    print("wrote", path)


if __name__ == "__main__":
    dump_prepared("simple_switch")
    dump_prepared("empty_nodes")
    dump_prepared("missing_ids", assign_missing_ids=True)
    dump_prepared("multi_lang_comma")
    dump_prepared("nested_tspan_style", nested_strategy="preserve_style")
    dump_prepared("nested_tspan_style", nested_strategy="flatten")
    dump_extract("simple_switch")
    dump_extract("header_subtitle")
```

```bash
# First time (or intentional behaviour change):
python -m tests.scripts.update_goldens

# Normal CI / local:
pytest tests/test_preparation_golden.py tests/test_extraction_golden.py tests/test_nested_golden.py -v
```

---

## 9. Minimal fixture examples

**`simple_switch.svg`** — one fallback + one language  

**`multi_lang_comma.svg`** — `systemLanguage="ar, fr"`  

**`nested_tspan_style.svg`** — styled nested tspan  

**`empty_nodes.svg`** — empty `<tspan id="x"/>`  

**`missing_ids.svg`** — `<text>` / `<tspan>` without `id`  

**`header_subtitle.svg`** — `g#header` + `g#subtitle` switches  

**`invalid_dup_lang.svg`** — two `systemLanguage="ar"` in one switch  

Keep fixtures small (one concern each).

---

## 10. Workflow tied to the refactor

| Step | Action |
|------|--------|
| Before code changes | Generate goldens from **current** main |
| During refactor | Run golden tests after each phase |
| Failures | Diff actual vs golden; fix code, not goldens (unless intentional) |
| Intentional behaviour change | Update goldens in a **separate** commit with explanation |

---

## 11. CI snippet

```yaml
# example
- name: Golden fixtures
  run: pytest tests/test_preparation_golden.py tests/test_extraction_golden.py tests/test_nested_golden.py -v
```

---

**Success criterion:** After the preparation / nested / extraction refactors, all golden tests pass with **zero** golden file updates.
