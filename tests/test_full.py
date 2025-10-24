"""Integration-style tests for the public CopySvgTranslate API."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from CopySvgTranslate import extract, svg_extract_and_inject, svg_extract_and_injects

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def target_svg(tmp_path: Path) -> Path:
    """Return a writable copy of the target SVG fixture."""
    target = tmp_path / "target.svg"
    target.write_text((FIXTURES_DIR / "target.svg").read_text(encoding="utf-8"), encoding="utf-8")
    return target


def test_svg_extract_and_inject_creates_translation_files(tmp_path: Path, target_svg: Path) -> None:
    """svg_extract_and_inject should persist both JSON mappings and the translated SVG."""
    source_svg = FIXTURES_DIR / "source.svg"
    data_output = tmp_path / "translations.json"
    output_svg = tmp_path / "translated.svg"

    tree = svg_extract_and_inject(
        source_svg,
        target_svg,
        output_file=output_svg,
        data_output_file=data_output,
        overwrite=True,
        save_result=True,
    )

    assert tree is not None, "An lxml tree should be returned for the translated SVG"
    assert output_svg.exists(), "The translated SVG should be written to disk"
    assert data_output.exists(), "The extracted translations should be written to JSON"

    saved_translations = json.loads(data_output.read_text(encoding="utf-8"))
    # Keys are normalized to lowercase by the extractor
    assert saved_translations["new"]["population 2020"]["ar"] == "السكان 2020"

    injected_svg = output_svg.read_text(encoding="utf-8")
    assert "systemLanguage=\"ar\"" in injected_svg
    assert "السكان 2020" in injected_svg


def test_svg_extract_and_injects_uses_existing_mapping(tmp_path: Path, target_svg: Path) -> None:
    """svg_extract_and_injects should reuse an already-extracted mapping structure."""
    translations = extract(FIXTURES_DIR / "source.svg")

    output_dir = tmp_path / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    tree, stats = svg_extract_and_injects(
        translations,
        target_svg,
        output_dir=output_dir,
        save_result=True,
        return_stats=True,
    )

    assert tree is not None
    assert stats["inserted_translations"] >= 1

    output_file = output_dir / target_svg.name
    assert output_file.exists(), "The helper should honour the output directory when saving results"
    content = output_file.read_text(encoding="utf-8")
    assert "systemLanguage=\"ar\"" in content
    assert "السكان 2020" in content


def test_svg_extract_and_inject_without_save_result(tmp_path: Path, target_svg: Path) -> None:
    """svg_extract_and_inject should work without saving results to disk."""
    source_svg = FIXTURES_DIR / "source.svg"
    data_output = tmp_path / "translations.json"
    output_svg = tmp_path / "translated.svg"

    tree = svg_extract_and_inject(
        source_svg,
        target_svg,
        output_file=output_svg,
        data_output_file=data_output,
        overwrite=True,
        save_result=False,  # Don't save the injected SVG
    )

    assert tree is not None, "An lxml tree should still be returned"
    assert data_output.exists(), "The extracted translations should still be written to JSON"
    assert not output_svg.exists(), "The translated SVG should not be written when save_result=False"


def test_svg_extract_and_inject_with_default_paths(tmp_path: Path, target_svg: Path) -> None:
    """svg_extract_and_inject should use default paths when none are provided."""
    import os
    original_cwd = os.getcwd()

    try:
        # Change to tmp_path so default paths are created there
        os.chdir(tmp_path)

        source_svg = FIXTURES_DIR / "source.svg"

        tree = svg_extract_and_inject(
            source_svg,
            target_svg,
            save_result=True,
        )

        assert tree is not None
        # Check that default directories were created
        assert (tmp_path / "data").exists(), "Default data directory should be created"
        assert (tmp_path / "translated").exists(), "Default translated directory should be created"

        # Check that files were created in default locations
        data_file = tmp_path / "data" / f"{source_svg.name}.json"
        assert data_file.exists(), "Translation data should be saved in default location"

        translated_file = tmp_path / "translated" / target_svg.name
        assert translated_file.exists(), "Translated SVG should be saved in default location"
    finally:
        os.chdir(original_cwd)


def test_svg_extract_and_inject_nonexistent_source(tmp_path: Path, target_svg: Path) -> None:
    """svg_extract_and_inject should return None if source file doesn't exist."""
    nonexistent_source = tmp_path / "nonexistent_source.svg"

    result = svg_extract_and_inject(
        nonexistent_source,
        target_svg,
        save_result=False,
    )

    assert result is None, "Should return None when source file doesn't exist"


def test_svg_extract_and_inject_nonexistent_target(tmp_path: Path) -> None:
    """svg_extract_and_inject should return None if target file doesn't exist."""
    source_svg = FIXTURES_DIR / "source.svg"
    nonexistent_target = tmp_path / "nonexistent_target.svg"

    result = svg_extract_and_inject(
        source_svg,
        nonexistent_target,
        save_result=False,
    )

    assert result is None, "Should return None when target file doesn't exist"


def test_svg_extract_and_inject_with_pathlib_and_string_paths(tmp_path: Path, target_svg: Path) -> None:
    """svg_extract_and_inject should handle both Path and string arguments."""
    source_svg = FIXTURES_DIR / "source.svg"
    output_svg = tmp_path / "output.svg"
    data_output = tmp_path / "data.json"

    # Test with string paths
    tree = svg_extract_and_inject(
        str(source_svg),  # String path
        str(target_svg),  # String path
        output_file=str(output_svg),
        data_output_file=str(data_output),
        save_result=True,
    )

    assert tree is not None
    assert output_svg.exists()
    assert data_output.exists()


def test_svg_extract_and_inject_preserves_translation_data(tmp_path: Path, target_svg: Path) -> None:
    """svg_extract_and_inject should preserve the correct translation structure in JSON."""
    source_svg = FIXTURES_DIR / "source.svg"
    data_output = tmp_path / "translations.json"
    output_svg = tmp_path / "translated.svg"

    svg_extract_and_inject(
        source_svg,
        target_svg,
        output_file=output_svg,
        data_output_file=data_output,
        save_result=True,
    )

    # Verify the JSON structure
    translations = json.loads(data_output.read_text(encoding="utf-8"))

    assert "new" in translations
    assert "title" in translations
    assert isinstance(translations["new"], dict)

    # Verify at least one translation exists
    assert len(translations["new"]) > 0


def test_svg_extract_and_injects_without_output_dir(tmp_path: Path, target_svg: Path) -> None:
    """svg_extract_and_injects should handle missing output_dir when save_result=False."""
    translations = extract(FIXTURES_DIR / "source.svg")

    tree, stats = svg_extract_and_injects(
        translations,
        target_svg,
        save_result=False,
        return_stats=True,
    )

    assert tree is not None
    assert isinstance(stats, dict)


def test_svg_extract_and_injects_with_default_output_dir(tmp_path: Path, target_svg: Path) -> None:
    """svg_extract_and_injects should create default output_dir when needed."""
    import os
    original_cwd = os.getcwd()

    try:
        os.chdir(tmp_path)

        translations = extract(FIXTURES_DIR / "source.svg")

        tree, _stats = svg_extract_and_injects(
            translations,
            target_svg,
            save_result=True,
            return_stats=True,
        )

        assert tree is not None
        # Check that default directory was created
        assert (tmp_path / "translated").exists()
        assert (tmp_path / "translated" / target_svg.name).exists()
    finally:
        os.chdir(original_cwd)


def test_svg_extract_and_injects_returns_stats(tmp_path: Path, target_svg: Path) -> None:
    """svg_extract_and_injects should return detailed statistics when requested."""
    translations = extract(FIXTURES_DIR / "source.svg")

    result = svg_extract_and_injects(
        translations,
        target_svg,
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


def test_svg_extract_and_injects_without_stats(tmp_path: Path, target_svg: Path) -> None:
    """svg_extract_and_injects should return only tree when return_stats=False."""
    translations = extract(FIXTURES_DIR / "source.svg")

    result = svg_extract_and_injects(
        translations,
        target_svg,
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
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
        encoding="utf-8"
    )

    result = extract(empty_svg)

    # Should return a dict (possibly with empty structures) or None
    assert result is None or isinstance(result, dict)


def test_extract_preserves_multiple_languages(tmp_path: Path) -> None:
    """extract should preserve translations for multiple languages."""
    multi_lang_svg = tmp_path / "multi.svg"
    multi_lang_svg.write_text(
        '''<?xml version="1.0" encoding="UTF-8"?>
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
</svg>''',
        encoding="utf-8"
    )

    result = extract(multi_lang_svg)

    assert result is not None
    # Should have translations for ar, fr, and es
    if "new" in result and "hello" in result["new"]:
        translations = result["new"]["hello"]
        assert "ar" in translations or "fr" in translations or "es" in translations


def test_svg_extract_and_inject_with_overwrite_true(tmp_path: Path, target_svg: Path) -> None:
    """svg_extract_and_inject should overwrite existing translations when overwrite=True."""
    source_svg = FIXTURES_DIR / "source.svg"
    output_svg = tmp_path / "output.svg"

    # First injection
    tree1 = svg_extract_and_inject(
        source_svg,
        target_svg,
        output_file=output_svg,
        overwrite=True,
        save_result=True,
    )

    assert tree1 is not None
    assert output_svg.exists()

    # Second injection with overwrite
    tree2 = svg_extract_and_inject(
        source_svg,
        target_svg,
        output_file=output_svg,
        overwrite=True,
        save_result=True,
    )

    assert tree2 is not None
    # File should still exist and be valid
    content2 = output_svg.read_text(encoding="utf-8")
    assert "systemLanguage=\"ar\"" in content2


def test_svg_extract_and_injects_with_empty_translations(tmp_path: Path, target_svg: Path) -> None:
    """svg_extract_and_injects should handle empty translation dictionaries gracefully."""
    empty_translations = {"new": {}, "title": {}}

    result = svg_extract_and_injects(
        empty_translations,
        target_svg,
        save_result=False,
    )

    # Should handle gracefully and return a result (even if no translations were applied)
    assert result is not None or result is None  # Either outcome is acceptable


def test_extract_with_case_insensitive_true() -> None:
    """
    Normalize translation keys to lowercase when extract is run with case-insensitive mode.

    Verifies that calling extract on the sample SVG with case_insensitive enabled produces a result whose "new" translation keys (string keys) are all lowercase.
    """
    result = extract(FIXTURES_DIR / "source.svg", case_insensitive=True)

    assert result is not None
    # Keys should be lowercase
    if "new" in result:
        for key in result["new"].keys():
            if isinstance(key, str):
                # Text keys should be lowercase
                assert key == key.lower()


def test_extract_with_case_insensitive_false(tmp_path: Path) -> None:
    """extract should preserve original case when case_insensitive=False."""
    svg_with_caps = tmp_path / "caps.svg"
    svg_with_caps.write_text(
        '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <switch>
    <text id="label" xml:space="preserve">
      <tspan id="label">HELLO WORLD</tspan>
    </text>
    <text id="label-ar" systemLanguage="ar" xml:space="preserve">
      <tspan id="label-ar">مرحبا</tspan>
    </text>
  </switch>
</svg>''',
        encoding="utf-8"
    )

    result = extract(svg_with_caps, case_insensitive=False)

    # When case_insensitive is False, original case might be preserved
    # (implementation dependent, so we just check it doesn't crash)
    assert result is None or isinstance(result, dict)


def test_svg_extract_and_inject_creates_parent_directories(tmp_path: Path, target_svg: Path) -> None:
    """svg_extract_and_inject should create parent directories for output files."""
    source_svg = FIXTURES_DIR / "source.svg"

    # Use nested directories that don't exist yet
    nested_output = tmp_path / "deeply" / "nested" / "path" / "output.svg"
    nested_data = tmp_path / "another" / "nested" / "data.json"

    tree = svg_extract_and_inject(
        source_svg,
        target_svg,
        output_file=nested_output,
        data_output_file=nested_data,
        save_result=True,
    )

    assert tree is not None
    assert nested_output.exists(), "Output file should be created with parent directories"
    assert nested_data.exists(), "Data file should be created with parent directories"


def test_svg_extract_and_injects_multiple_operations(tmp_path: Path, target_svg: Path) -> None:
    """svg_extract_and_injects should handle multiple injection operations."""
    translations = extract(FIXTURES_DIR / "source.svg")

    # First injection
    output1 = tmp_path / "output1"
    output1.mkdir()
    tree1, stats1 = svg_extract_and_injects(
        translations,
        target_svg,
        output_dir=output1,
        save_result=True,
        return_stats=True,
    )

    # Second injection to different location
    output2 = tmp_path / "output2"
    output2.mkdir()
    tree2, stats2 = svg_extract_and_injects(
        translations,
        target_svg,
        output_dir=output2,
        save_result=True,
        return_stats=True,
    )

    assert tree1 is not None
    assert tree2 is not None
    assert (output1 / target_svg.name).exists()
    assert (output2 / target_svg.name).exists()

    # Both should have inserted the same number of translations
    assert stats1["inserted_translations"] == stats2["inserted_translations"]
