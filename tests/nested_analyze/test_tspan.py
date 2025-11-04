"""Additional comprehensive pytest tests for CopySVGTranslation."""

import sys
from pathlib import Path
from lxml import etree

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySVGTranslation.nested_analyze.find_nested import fix_nested_tspans

SVG_NS = "http://www.w3.org/2000/svg"


def _make_svg(content: str):
    """Helper to wrap content in <svg> for parsing."""
    xml = f'<svg xmlns="{SVG_NS}">{content}</svg>'
    return etree.fromstring(xml.encode("utf-8"))


def test_fix_nested_tspans_single_nested():
    svg = _make_svg(
        '<text><tspan x="0" y="10">A<tspan>B</tspan>C</tspan></text>'
    )
    fixed = fix_nested_tspans(svg)
    tspans = svg.findall(f".//{{{SVG_NS}}}tspan")
    # only one tspan should remain
    assert len(tspans) == 1
    assert tspans[0].text == "ABC"
    assert tspans[0].tail is None


def test_fix_nested_tspans_multiple_nested():
    svg = _make_svg(
        '<text><tspan><tspan>inner1</tspan><tspan>inner2</tspan></tspan></text>'
    )
    fixed = fix_nested_tspans(svg)
    tspans = fixed.findall(f".//{{{SVG_NS}}}tspan")
    assert len(tspans) == 1
    assert tspans[0].text == "inner1inner2"


def test_fix_nested_tspans_preserves_siblings():
    svg = _make_svg(
        '<text>'
        '<tspan>A<tspan>B</tspan></tspan>'
        '<tspan>C<tspan>D</tspan></tspan>'
        '</text>'
    )
    fixed = fix_nested_tspans(svg)
    tspans = fixed.findall(f".//{{{SVG_NS}}}tspan")
    texts = [t.text for t in tspans]
    assert texts == ["AB", "CD"]


def test_no_nested_tspans_unchanged():
    svg = _make_svg('<text><tspan>A</tspan><tspan>B</tspan></text>')
    original = etree.tostring(svg)
    fix_nested_tspans(svg)
    after = etree.tostring(svg)
    assert original == after


def test_nested_tspans_with_tail_text():
    svg = _make_svg(
        '<text><tspan>start<tspan>mid</tspan>end</tspan></text>'
    )
    fix_nested_tspans(svg)
    tspan = svg.find(f".//{{{SVG_NS}}}tspan")
    assert tspan.text == "startmidend"
