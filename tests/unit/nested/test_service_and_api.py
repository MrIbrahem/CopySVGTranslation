from __future__ import annotations

from pathlib import Path

from lxml import etree

from CopySVGTranslation import (
    NestedStructureService,
    RepairResult,
    SVGTranslationService,
)
from CopySVGTranslation.result import OperationResult

SVG_NS = "http://www.w3.org/2000/svg"


def _svg(inner: str) -> str:
    return f'<svg xmlns="{SVG_NS}">{inner}</svg>'


def test_nested_structure_service_analyze(tmp_path: Path):
    src = tmp_path / "input.svg"
    src.write_text(
        _svg("""<text id="t1"><tspan><tspan style="font-weight: 700;">Bold</tspan></tspan></text>"""),
        encoding="utf-8",
    )

    service = NestedStructureService()
    findings = service.analyze_file(src)
    assert len(findings) == 1
    assert "Bold" in findings[0]


def test_nested_structure_service_ignores_link_wrapping_tspan(tmp_path: Path):
    """A valid link wrapper is not repairable nesting and must be ignored."""
    src = tmp_path / "input.svg"
    src.write_text(
        _svg("""<text id="t1"><a href="outer"><tspan style="font-weight: 700;">Nested</tspan></a></text>"""),
        encoding="utf-8",
    )

    service = NestedStructureService()

    assert service.analyze_file(src) == []

    repair_result = service.repair_file(src)
    assert repair_result.success is True
    assert repair_result.len_tags_before_fix == 0
    assert repair_result.len_tags_after_fix == 0
    assert repair_result.len_tags_fixed == 0


def test_nested_structure_service_ignores_link_wrapping_text_and_tspan(tmp_path: Path):
    """The clickable title structure from OWID SVGs must not be a false hit."""
    src = tmp_path / "input.svg"
    src.write_text(
        _svg(
            """<a href="https://example.org/chart" id="title"><text><tspan id="trsvg1">Chart title</tspan></text></a>"""
        ),
        encoding="utf-8",
    )

    service = NestedStructureService()

    assert service.analyze_file(src) == []


def test_nested_structure_service_detects_link_inside_tspan(tmp_path: Path):
    """A link inside text content remains repairable nested structure."""
    src = tmp_path / "input.svg"
    src.write_text(
        _svg("""<text id="t1"><tspan>Read <a href="inner">more</a></tspan></text>"""),
        encoding="utf-8",
    )

    service = NestedStructureService(strategy="flatten")
    findings = service.analyze_file(src)

    assert len(findings) == 1
    assert findings[0].startswith("<tspan")
    assert "<a" in findings[0]

    repair_result = service.repair_file(src)
    assert repair_result.success is True
    assert repair_result.len_tags_before_fix == 1
    assert repair_result.len_tags_after_fix == 0
    assert repair_result.len_tags_fixed == 1


def test_nested_structure_service_repair_in_place():
    root = etree.fromstring(
        _svg("""<text id="t1"><tspan><tspan style="font-weight: 700;">Bold</tspan></tspan></text>""")
    )
    service = NestedStructureService()
    result = service.repair_root(root)
    assert isinstance(result, RepairResult)
    assert result.success is True
    assert result.len_tags_before_fix == 1
    assert result.len_tags_after_fix == 0


def test_nested_structure_service_repair_file(tmp_path: Path):
    src = tmp_path / "input.svg"
    dst = tmp_path / "output.svg"
    src.write_text(
        _svg("""<text id="t1"><tspan><tspan style="font-weight: 700;">Bold</tspan></tspan></text>"""),
        encoding="utf-8",
    )

    service = NestedStructureService(strategy="preserve_style")
    res = service.repair_file(src, dst)
    assert isinstance(res, RepairResult)
    assert res.success is True
    assert res.len_tags_before_fix == 1
    assert res.len_tags_after_fix == 0
    assert dst.exists()

    # Parse dst and verify content/style are preserved
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    tree = etree.parse(str(dst), parser)
    root = tree.getroot()
    tspans = root.findall(f".//{{{SVG_NS}}}tspan")
    assert len(tspans) > 0
    has_style = any("font-weight: 700;" in (t.get("style") or "") and t.text == "Bold" for t in tspans)
    assert has_style is True


def test_svg_translation_service_analyze_nested(tmp_path: Path):
    src = tmp_path / "input.svg"
    src.write_text(
        _svg("""<text id="t1"><tspan><tspan style="font-weight: 700;">Bold</tspan></tspan></text>"""),
        encoding="utf-8",
    )

    service = SVGTranslationService()
    res = service.analyze_nested(src)
    assert isinstance(res, OperationResult)
    assert res.success is True
    assert len(res.data) == 1


def test_svg_translation_service_repair_nested(tmp_path: Path):
    src = tmp_path / "input.svg"
    dst = tmp_path / "output.svg"
    src.write_text(
        _svg("""<text id="t1"><tspan><tspan style="font-weight: 700;">Bold</tspan></tspan></text>"""),
        encoding="utf-8",
    )

    service = SVGTranslationService()
    res = service.repair_nested(src, output=dst, strategy="preserve_style")
    assert isinstance(res, OperationResult)
    assert res.success is True
    assert dst.exists()

    # Verify that analyzing the output file yields no nested elements
    res_after = service.analyze_nested(dst)
    assert res_after.success is True
    assert len(res_after.data) == 0
