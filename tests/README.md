**Full Tests Design Structure**

```
tests/
├── conftest.py
├── fixtures/
│   ├── __init__.py
│   ├── svg/
│   │   ├── simple_switch.svg
│   │   ├── multi_tspan.svg
│   │   ├── multi_lang.svg
│   │   ├── nested_tspan.svg
│   │   ├── nested_styled.svg
│   │   ├── year_title.svg
│   │   ├── no_switch.svg
│   │   ├── with_tref.svg
│   │   ├── comma_languages.svg
│   │   └── empty.svg
│   └── mappings/
│       ├── basic.json
│       ├── multi_lang.json
│       └── year_title.json
│
├── unit/
│   ├── core/
│   │   ├── test_mapping.py
│   │   ├── test_text_node.py
│   │   └── test_switch_node.py
│   ├── utils/
│   │   ├── test_text.py
│   │   └── test_xml.py
│   ├── titles/
│   │   └── test_year_handler.py
│   ├── nested/
│   │   ├── test_detector.py
│   │   └── test_flattener.py
│   ├── extraction/
│   │   ├── test_extractor.py
│   │   └── test_strategies.py
│   ├── injection/
│   │   ├── test_id_manager.py
│   │   ├── test_translation_applier.py
│   │   ├── test_switch_processor.py
│   │   ├── test_injector.py
│   │   └── steps/
│   │       ├── test_load.py
│   │       ├── test_validate.py
│   │       ├── test_normalize_tspans.py
│   │       ├── test_assign_ids.py
│   │       ├── test_split_languages.py
│   │       └── test_reorder.py
│   ├── io/
│   │   ├── test_svg_document.py
│   │   └── test_mapping_store.py
│   ├── test_config.py
│   ├── test_result.py
│   └── test_exceptions.py
│
├── integration/
│   ├── test_service_extract.py
│   ├── test_service_inject.py
│   ├── test_service_extract_and_inject.py
│   ├── test_prepare_only.py
│   └── test_roundtrip.py
│
├── legacy/
│   ├── test_extract.py
│   ├── test_inject.py
│   └── test_workflows.py
│
└── contract/
    ├── test_public_api.py
    └── test_deprecation_warnings.py
```

---

### 1. `conftest.py` — shared fixtures

```python
# tests/conftest.py
from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree

from CopySVGTranslation import TranslationConfig, SVGTranslationService
from CopySVGTranslation.core.mapping import TranslationMapping

FIXTURES = Path(__file__).parent / "fixtures"
SVG_DIR = FIXTURES / "svg"
MAP_DIR = FIXTURES / "mappings"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def svg_dir() -> Path:
    return SVG_DIR


@pytest.fixture
def map_dir() -> Path:
    return MAP_DIR


@pytest.fixture
def default_config() -> TranslationConfig:
    return TranslationConfig(
        case_insensitive=True,
        overwrite=False,
        pretty_print=True,
        nested_strategy="preserve_style",
        enable_year_titles=True,
        auto_save=False,
    )


@pytest.fixture
def service(default_config: TranslationConfig) -> SVGTranslationService:
    return SVGTranslationService(default_config)


@pytest.fixture
def sample_mapping() -> TranslationMapping:
    return TranslationMapping(
        new={
            "hello": {"ar": "مرحبا", "es": "hola"},
            "world": {"ar": "العالم", "es": "mundo"},
        }
    )


def load_svg_root(path: Path) -> etree._Element:
    tree = etree.parse(str(path))
    root = tree.getroot()
    assert root is not None
    return root


@pytest.fixture
def svg_path(svg_dir: Path):
    """Factory: svg_path("simple_switch.svg") -> Path."""
    def _make(name: str) -> Path:
        path = svg_dir / name
        assert path.exists(), f"Missing fixture: {path}"
        return path
    return _make
```

---

### 2. Fixture SVG set (what each file is for)

| File                  | Purpose                                         |
| --------------------- | ----------------------------------------------- |
| `simple_switch.svg`   | One switch, one fallback text, one language     |
| `multi_tspan.svg`     | Fallback with several tspans + matching ids     |
| `multi_lang.svg`      | Several `systemLanguage` nodes                  |
| `nested_tspan.svg`    | Nested tspans without extra styles              |
| `nested_styled.svg`   | Nested tspans with `font-weight` etc.           |
| `year_title.svg`      | Title ending with a year                        |
| `no_switch.svg`       | `<text>` outside switch (preparation must wrap) |
| `with_tref.svg`       | Contains `<tref>` → must raise                  |
| `comma_languages.svg` | `systemLanguage="ar,fr"` → split step           |
| `empty.svg`           | No text nodes                                   |

---

### 3. Unit tests — what to cover

#### `unit/core/`

| File                  | Focus                                                                      |
| --------------------- | -------------------------------------------------------------------------- |
| `test_mapping.py`     | `from_any`, `add`, `merge`, `lookup`, `is_empty`, `to_json`, case handling |
| `test_text_node.py`   | `texts()`, `set_texts()`, language property, clone, tspans                 |
| `test_switch_node.py` | `fallback()`, `existing_languages()`, `find_by_language()`, `reorder()`    |

#### `unit/utils/`

| File           | Focus                                                            |
| -------------- | ---------------------------------------------------------------- |
| `test_text.py` | `normalize_text`, `normalize_lang`, `split_lang_list` edge cases |
| `test_xml.py`  | `collect_ids`, `extract_root_languages`, `sort_switch_children`  |

#### `unit/titles/`

| File                   | Focus                                                                               |
| ---------------------- | ----------------------------------------------------------------------------------- |
| `test_year_handler.py` | `match_year`, templates at extract time, expand at inject time, disabled via config |

#### `unit/nested/`

| File                | Focus                                                                       |
| ------------------- | --------------------------------------------------------------------------- |
| `test_detector.py`  | finds nested nodes; empty when flat                                         |
| `test_flattener.py` | `split_nested_tspans`, `preserve_style`, `flatten`, `raise`; `<a>` handling |

#### `unit/extraction/`

| File                 | Focus                                                                   |
| -------------------- | ----------------------------------------------------------------------- |
| `test_strategies.py` | `ByTspanIdStrategy`, `ByPositionStrategy`, `CompositeMatchingStrategy`  |
| `test_extractor.py`  | builds correct `TranslationMapping` from fixtures; empty / missing file |

#### `unit/injection/`

| File                          | Focus                                     |
| ----------------------------- | ----------------------------------------- |
| `test_id_manager.py`          | unique ids, clone ids, collision suffixes |
| `test_translation_applier.py` | insert / update / skip for one language   |
| `test_switch_processor.py`    | one switch, multiple languages, stats     |
| `test_injector.py`            | full inject on prepared tree; save path   |
| `steps/test_*.py`             | each preparation step in isolation        |

#### `unit/io/`

| File                    | Focus                                   |
| ----------------------- | --------------------------------------- |
| `test_svg_document.py`  | load, namespace fix, save, missing file |
| `test_mapping_store.py` | load, load_many merge, save roundtrip   |

#### Root unit

| File                 | Focus                                |
| -------------------- | ------------------------------------ |
| `test_config.py`     | defaults, `with_updates`             |
| `test_result.py`     | `ok` / `fail` helpers                |
| `test_exceptions.py` | codes, message formatting, hierarchy |

---

### 4. Integration tests

| File                                 | Scenario                                         |
| ------------------------------------ | ------------------------------------------------ |
| `test_service_extract.py`            | `service.extract()` success + failure paths      |
| `test_service_inject.py`             | inject with/without overwrite, stats             |
| `test_service_extract_and_inject.py` | end-to-end copy translations source → target     |
| `test_prepare_only.py`               | structure normalized, no new languages           |
| `test_roundtrip.py`                  | extract → inject → extract again; mapping stable |

Use real fixture files and temp dirs (`tmp_path`).

---

### 5. Legacy tests

| File              | Purpose                                       |
| ----------------- | --------------------------------------------- |
| `test_extract.py` | old `extract()` still returns dict / None     |
| `test_inject.py`  | old `inject()` return shapes + `return_stats` |

All should assert `pytest.warns(DeprecationWarning)`.

Mark with `@pytest.mark.legacy`.

---

### 6. Contract tests

| File                           | Purpose                                    |
| ------------------------------ | ------------------------------------------ |
| `test_public_api.py`           | every name in root `__all__` is importable |
| `test_deprecation_warnings.py` | legacy entry points always warn            |

---

### 7. Example test patterns

**Unit — pure logic**

```python
# tests/unit/titles/test_year_handler.py
from CopySVGTranslation.titles import YearTitleHandler
from CopySVGTranslation.core.mapping import TranslationMapping
from CopySVGTranslation import TranslationConfig

def test_build_templates():
    mapping = TranslationMapping(new={
        "COVID-19 pandemic 2020": {"ar": "جائحة كوفيد 2020"},
    })
    handler = YearTitleHandler(TranslationConfig(enable_year_titles=True))
    handler.build_templates(mapping)
    assert "COVID-19 pandemic {year}" in mapping.title_new
    assert mapping.title_new["COVID-19 pandemic {year}"]["ar"] == "جائحة كوفيد {year}"
```

**Unit — strategy**

```python
# tests/unit/extraction/test_strategies.py
def test_by_position_matches_in_order(default_node, translated_node):
    strategy = ByPositionStrategy()
    matches = strategy.match(default_node, translated_node)
    assert [m.default_text for m in matches] == ["hello", "world"]
```

**Integration — service**

```python
# tests/integration/test_service_extract_and_inject.py
def test_extract_and_inject(service, svg_path, tmp_path):
    output = tmp_path / "translated.svg"
    output.write_text(svg_path("simple_switch.svg").read_text(encoding="utf-8"), encoding="utf-8")

    result = service.extract_and_inject(
        source=svg_path("multi_lang.svg"),
        output=output,
        save=True,
    )

    assert result.success
    assert output.exists()
    assert result.stats is not None
    assert result.stats.inserted_translations >= 1
```

---

### 8. Markers & pytest config (already in `pyproject.toml`)

```toml
[tool.pytest.ini_options]
markers = [
    "todo: work in progress",
]
```

Run subsets:

```bash
pytest                         # all
pytest tests/unit              # fast
pytest tests/integration       # slower, file-based
pytest -m "not todo"           # skip unfinished
```

---

### 9. Coverage goals

| Area                                | Target |
| ----------------------------------- | ------ |
| `core`, `utils`, `titles`, `nested` | ≥ 95%  |
| `extraction`, `injection`           | ≥ 90%  |
| `service`, `io`                     | ≥ 85%  |

---

### 10. Design principles

1. **Pyramid** — many unit tests, fewer integration, thin legacy/contract layers.
2. **Fixtures over inline XML** — reusable SVGs in `tests/fixtures/svg/`.
3. **No network, no real cwd pollution** — use `tmp_path`.
4. **Test behaviour, not private names** — prefer public service/extractor APIs; step tests may use pipeline internals.
5. **Warnings are part of the contract** — legacy tests must assert deprecation.
6. **Deterministic** — sort orders, ids, and language sets should be asserted explicitly.

This structure matches the redesigned package layout and supports the Phase 1→3 migration without rewriting the suite later.
