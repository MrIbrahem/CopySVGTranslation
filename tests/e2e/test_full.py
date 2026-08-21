"""Integration-style tests for the public CopySVGTranslation API."""

from __future__ import annotations

from pathlib import Path

import pytest

from CopySVGTranslation import SVGTranslationService, TranslationConfig
from CopySVGTranslation.core.mapping import InjectorData


@pytest.fixture()
def target_svg(tmp_path: Path, fixtures_dir) -> Path:
    """Return a writable copy of the target SVG fixture."""
    target = tmp_path / "target.svg"
    target.write_text((fixtures_dir / "target.svg").read_text(encoding="utf-8"), encoding="utf-8")
    return target


def test_inject_uses_existing_mapping(tmp_path: Path, target_svg: Path, fixtures_dir) -> None:
    """inject should reuse an already-extracted mapping structure."""
    service = SVGTranslationService()
    _extract_result = service.extract(fixtures_dir / "source.svg")
    assert _extract_result.success

    _output_dir = tmp_path / "outputs"
    _output_dir.mkdir(parents=True, exist_ok=True)
    output_file = _output_dir / target_svg.name

    result = service.inject(
        svg_path=target_svg,
        mapping=_extract_result.data,
        output=output_file,
        save=True,
    )

    assert result.success
    assert isinstance(result.data, InjectorData)
    tree = result.data.tree
    stats = result.data.inject_stats.to_json()

    assert tree is not None
    assert stats["inserted_translations"] >= 1

    assert output_file.exists(), "The helper should honour the output directory when saving results"
    content = output_file.read_text(encoding="utf-8")
    assert 'systemLanguage="ar"' in content
    assert "السكان 2020" in content


def test_inject_without_save_path(tmp_path: Path, target_svg: Path, fixtures_dir) -> None:
    """inject should handle save=False without output path."""
    service = SVGTranslationService()
    _extract_result = service.extract(fixtures_dir / "source.svg")
    assert _extract_result.success

    result = service.inject(
        svg_path=target_svg,
        mapping=_extract_result.data,
        save=False,
    )

    assert result.success
    assert result.data is not None
    assert result.data.tree is not None
    stats = result.data.inject_stats.to_json()
    assert isinstance(stats, dict)


def test_inject_returns_stats(tmp_path: Path, target_svg: Path, fixtures_dir) -> None:
    """inject should return detailed statistics."""
    service = SVGTranslationService()
    _extract_result = service.extract(fixtures_dir / "source.svg")
    assert _extract_result.success

    result = service.inject(
        svg_path=target_svg,
        mapping=_extract_result.data,
        output=target_svg,
    )

    assert result.success
    assert isinstance(result.data, InjectorData)
    stats = result.data.inject_stats.to_json()

    assert isinstance(stats, dict)
    # Verify expected stats keys
    expected_keys = ["inserted_translations", "updated_translations", "processed_switches"]
    for key in expected_keys:
        assert key in stats, f"Stats should contain '{key}' key"


def test_inject_without_stats(tmp_path: Path, target_svg: Path, fixtures_dir) -> None:
    """inject always returns InjectorData (stats are always available)."""
    service = SVGTranslationService()
    _extract_result = service.extract(fixtures_dir / "source.svg")
    assert _extract_result.success

    result = service.inject(
        svg_path=target_svg,
        mapping=_extract_result.data,
        output=target_svg,
    )

    assert result.success
    assert result.data is not None
    assert result.data.tree is not None


def test_extract_with_pathlib_path(fixtures_dir) -> None:
    """extract should work with pathlib.Path objects."""
    source_path = fixtures_dir / "source.svg"

    service = SVGTranslationService()
    _result = service.extract(source_path)
    assert _result.success
    assert _result.data is not None
    result = _result.data.to_json()

    assert result is not None
    assert isinstance(result, dict)


def test_extract_with_string_path(fixtures_dir) -> None:
    """extract should work with string paths."""
    source_path = str(fixtures_dir / "source.svg")

    service = SVGTranslationService()
    _result = service.extract(source_path)
    assert _result.success
    assert _result.data is not None
    result = _result.data.to_json()

    assert result is not None
    assert isinstance(result, dict)


def test_extract_empty_svg(tmp_path: Path) -> None:
    """extract should handle SVG files with no translations gracefully."""
    empty_svg = tmp_path / "empty.svg"
    empty_svg.write_text(
        '<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg"></svg>', encoding="utf-8"
    )

    service = SVGTranslationService()
    result = service.extract(empty_svg)

    assert not result.success
    assert result.data is None


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

    service = SVGTranslationService()
    _result = service.extract(multi_lang_svg)
    assert _result.success
    assert _result.data is not None
    result = _result.data.to_json()

    # Should have translations for ar, fr, and es
    assert result == {
        "new": {"hello": {"ar": "مرحبا", "fr": "Bonjour", "es": "Hola"}},
        "tspans_by_id": {"label": "Hello"},
        "title_new": {},
        "meta": {},
        "error": "",
    }


def test_inject_with_empty_translations(tmp_path: Path, target_svg: Path) -> None:
    """inject should handle empty translation dictionaries gracefully."""
    empty_translations = {"new": {}}

    service = SVGTranslationService()
    result = service.inject(
        svg_path=target_svg,
        mapping=empty_translations,
        output=target_svg,
    )

    assert result.success
    assert result.data is not None
    stats = result.data.inject_stats.to_json()
    assert stats == {
        "all_languages_count": 0,
        "new_languages_count": 0,
        "processed_switches": 0,
        "inserted_translations": 0,
        "skipped_translations": 0,
        "updated_translations": 0,
        "languages_before": [],
        "languages_after": [],
    }


def test_extract_with_case_insensitive_true(fixtures_dir) -> None:
    """
    Normalize translation keys to lowercase when extract is run with case-insensitive mode.

    Verifies that calling extract on the sample SVG with case_insensitive enabled produces a result whose "new" translation keys (string keys) are all lowercase.
    """
    service = SVGTranslationService()
    _result = service.extract(fixtures_dir / "source.svg")
    assert _result.success
    assert _result.data is not None
    result = _result.data.to_json()

    assert result == {
        "new": {"population 2020": {"ar": "السكان 2020", "fr": "Population 2020 FR"}},
        "tspans_by_id": {"label": "Population 2020"},
        "title_new": {"population {year}": {"ar": "السكان {year}"}},
        "meta": {},
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

    service = SVGTranslationService(TranslationConfig(case_insensitive=False))
    _result = service.extract(svg_with_caps)
    assert _result.success
    assert _result.data is not None
    result = _result.data.to_json()

    assert result == {
        "new": {"HELLO WORLD": {"ar": "مرحبا"}},
        "tspans_by_id": {"label": "HELLO WORLD"},
        "title_new": {},
        "meta": {},
        "error": "",
    }


def test_inject_multiple_operations(tmp_path: Path, target_svg: Path, fixtures_dir) -> None:
    """inject should handle multiple injection operations."""
    service = SVGTranslationService()
    _extract_result = service.extract(fixtures_dir / "source.svg")
    assert _extract_result.success

    # First injection
    output1 = tmp_path / "output1"
    output1.mkdir()
    result1 = service.inject(
        svg_path=target_svg,
        mapping=_extract_result.data,
        output=output1 / target_svg.name,
        save=True,
    )
    assert result1.success
    assert result1.data is not None
    stats1 = result1.data.inject_stats.to_json()

    # Second injection to different location
    output2 = tmp_path / "output2"
    output2.mkdir()
    # Use a fresh service and re-read the original target_svg
    service2 = SVGTranslationService()
    result2 = service2.inject(
        svg_path=target_svg,
        mapping=_extract_result.data,
        output=output2 / target_svg.name,
        save=True,
    )
    assert result2.success
    assert result2.data is not None
    stats2 = result2.data.inject_stats.to_json()

    assert result1.data.tree is not None
    assert result2.data.tree is not None
    assert (output1 / target_svg.name).exists()
    assert (output2 / target_svg.name).exists()

    # Both should have inserted the same number of translations
    assert stats1["inserted_translations"] == stats2["inserted_translations"]

    assert stats1 == {
        "all_languages_count": 2,
        "new_languages_count": 2,
        "processed_switches": 1,
        "inserted_translations": 2,
        "skipped_translations": 0,
        "updated_translations": 0,
        "languages_before": [],
        "languages_after": ["ar", "fr"],
    }
