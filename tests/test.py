"""Integration-style tests for the public SvgTranslate API."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from SvgTranslate import extract, svg_extract_and_inject, svg_extract_and_injects

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
