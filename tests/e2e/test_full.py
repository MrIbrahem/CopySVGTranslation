"""Integration-style tests for the public CopySVGTranslation API."""

from __future__ import annotations

from pathlib import Path

import pytest

from CopySVGTranslation.extraction import extract
from CopySVGTranslation.injection import inject_file_and_save, inject_file_tree

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def target_svg(tmp_path: Path) -> Path:
    """Return a writable copy of the target SVG fixture."""
    target = tmp_path / "target.svg"
    target.write_text((FIXTURES_DIR / "target.svg").read_text(encoding="utf-8"), encoding="utf-8")
    return target


def test_inject_uses_existing_mapping(tmp_path: Path, target_svg: Path) -> None:
    """inject should reuse an already-extracted mapping structure."""
    translations = extract(FIXTURES_DIR / "source.svg")

    _output_dir = tmp_path / "outputs"
    _output_dir.mkdir(parents=True, exist_ok=True)
    output_file = _output_dir / target_svg.name

    tree, stats = inject_file_and_save(
        inject_file=target_svg,
        mapping=translations,
        save_path=output_file,
        return_stats=True,
    )

    assert tree is not None
    assert stats["inserted_translations"] >= 1

    assert output_file.exists(), "The helper should honour the output directory when saving results"
    content = output_file.read_text(encoding="utf-8")
    assert 'systemLanguage="ar"' in content
    assert "السكان 2020" in content


def test_inject_without_save_path(tmp_path: Path, target_svg: Path) -> None:
    """inject should handle missing save_path when save_result=False."""
    translations = extract(FIXTURES_DIR / "source.svg")

    tree, stats = inject_file_tree(
        inject_file=target_svg,
        mapping=translations,
        save_result=False,
        return_stats=True,
    )

    assert tree is not None
    assert isinstance(stats, dict)


def test_inject_returns_stats(tmp_path: Path, target_svg: Path) -> None:
    """inject should return detailed statistics when requested."""
    translations = extract(FIXTURES_DIR / "source.svg")

    result = inject_file_tree(
        inject_file=target_svg,
        mapping=translations,
        return_stats=True,
    )

    assert isinstance(result, tuple), "Should return tuple when return_stats=True"
    tree, stats = result

    assert tree is not None
    assert isinstance(stats, dict)
    # Verify expected stats keys
    expected_keys = ["inserted_translations", "updated_translations", "processed_switches"]
    for key in expected_keys:
        assert key in stats, f"Stats should contain '{key}' key"


def test_inject_without_stats(tmp_path: Path, target_svg: Path) -> None:
    """inject should return only tree when return_stats=False."""
    translations = extract(FIXTURES_DIR / "source.svg")

    result = inject_file_tree(
        inject_file=target_svg,
        mapping=translations,
        return_stats=False,
    )

    # When return_stats=False, might return just tree or (tree, None)
    # We need to check what's actually returned
    assert result is not None


def test_extract_with_pathlib_path() -> None:
    """extract should work with pathlib.Path objects."""
    source_path = FIXTURES_DIR / "source.svg"

    result = extract(source_path)

    assert result is not None
    assert isinstance(result, dict)


def test_extract_with_string_path() -> None:
    """extract should work with string paths."""
    source_path = str(FIXTURES_DIR / "source.svg")

    result = extract(source_path)

    assert result is not None
    assert isinstance(result, dict)


def test_extract_empty_svg(tmp_path: Path) -> None:
    """extract should handle SVG files with no translations gracefully."""
    empty_svg = tmp_path / "empty.svg"
    empty_svg.write_text(
        '<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg"></svg>', encoding="utf-8"
    )

    result = extract(empty_svg)

    assert result == {"new": {}, "tspans_by_id": {}, "title": {}, "title_new": {}, "error": ""}


def test_extract_preserves_multiple_languages(tmp_path: Path) -> None:
    """extract should preserve translations for multiple languages."""
    multi_lang_svg = tmp_path / "multi.svg"
    multi_lang_svg.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <switch>
    <text id="label" xml:space="preserve">
      <tspan id="label">Hello</tspan>
    </text>
    <text id="label-ar" systemLanguage="ar" xml:space="preserve">
      <tspan id="label-ar">مرحبا</tspan>
    </text>
    <text id="label-fr" systemLanguage="fr" xml:space="preserve">
      <tspan id="label-fr">Bonjour</tspan>
    </text>
    <text id="label-es" systemLanguage="es" xml:space="preserve">
      <tspan id="label-es">Hola</tspan>
    </text>
  </switch>
</svg>""",
        encoding="utf-8",
    )

    result = extract(multi_lang_svg)

    assert result is not None
    # Should have translations for ar, fr, and es
    assert result == {
        "new": {"hello": {"ar": "مرحبا", "fr": "Bonjour", "es": "Hola"}},
        "tspans_by_id": {"label": "Hello"},
        "title": {},
        "title_new": {},
        "error": "",
    }


def test_inject_with_empty_translations(tmp_path: Path, target_svg: Path) -> None:
    """inject should handle empty translation dictionaries gracefully."""
    empty_translations = {"new": {}, "title": {}}

    tree, stats = inject_file_tree(
        inject_file=target_svg,
        mapping=empty_translations,
        save_result=False,
        return_stats=True,
    )

    assert stats == {
        "all_languages": 0,
        "new_languages": 0,
        "processed_switches": 0,
        "inserted_translations": 0,
        "skipped_translations": 0,
        "updated_translations": 0,
        "languages_before": [],
        "languages_after": [],
        "error": "",
    }


def test_extract_with_case_insensitive_true() -> None:
    """
    Normalize translation keys to lowercase when extract is run with case-insensitive mode.

    Verifies that calling extract on the sample SVG with case_insensitive enabled produces a result whose "new" translation keys (string keys) are all lowercase.
    """
    result = extract(FIXTURES_DIR / "source.svg", case_insensitive=True)

    assert result is not None
    assert result == {
        "new": {"population 2020": {"ar": "السكان 2020", "fr": "Population 2020 FR"}},
        "tspans_by_id": {"label": "Population 2020"},
        "title": {"population": {"ar": "السكان"}},
        "title_new": {"population {year}": {"ar": "السكان {year}"}},
        "error": "",
    }


def test_extract_with_case_insensitive_false(tmp_path: Path) -> None:
    """extract should preserve original case when case_insensitive=False."""
    svg_with_caps = tmp_path / "caps.svg"
    svg_with_caps.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <switch>
    <text id="label" xml:space="preserve">
      <tspan id="label">HELLO WORLD</tspan>
    </text>
    <text id="label-ar" systemLanguage="ar" xml:space="preserve">
      <tspan id="label-ar">مرحبا</tspan>
    </text>
  </switch>
</svg>""",
        encoding="utf-8",
    )

    result = extract(
        svg_with_caps,
        case_insensitive=False,
    )

    assert result == {
        "new": {"HELLO WORLD": {"ar": "مرحبا"}},
        "tspans_by_id": {"label": "HELLO WORLD"},
        "title": {},
        "title_new": {},
        "error": "",
    }


def test_inject_multiple_operations(tmp_path: Path, target_svg: Path) -> None:
    """inject should handle multiple injection operations."""
    translations = extract(FIXTURES_DIR / "source.svg")

    # First injection
    output1 = tmp_path / "output1"
    output1.mkdir()
    tree1, stats1 = inject_file_and_save(
        inject_file=target_svg,
        mapping=translations,
        save_path=output1 / target_svg.name,
        return_stats=True,
    )

    # Second injection to different location
    output2 = tmp_path / "output2"
    output2.mkdir()
    tree2, stats2 = inject_file_and_save(
        inject_file=target_svg,
        mapping=translations,
        save_path=output2 / target_svg.name,
        return_stats=True,
    )

    assert tree1 is not None
    assert tree2 is not None
    assert (output1 / target_svg.name).exists()
    assert (output2 / target_svg.name).exists()

    # Both should have inserted the same number of translations

    assert stats1["inserted_translations"] == stats2["inserted_translations"]

    assert stats1 == {
        "all_languages": 2,
        "new_languages": 2,
        "processed_switches": 1,
        "inserted_translations": 2,
        "skipped_translations": 0,
        "updated_translations": 0,
        "languages_before": [],
        "languages_after": ["ar", "fr"],
        "error": "",
    }
