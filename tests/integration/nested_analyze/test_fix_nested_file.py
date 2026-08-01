from pathlib import Path

import pytest
from lxml import etree # type: ignore

from CopySVGTranslation.nested_analyze.find_nested import fix_nested_file, match_nested_tags

SVG_NS = "http://www.w3.org/2000/svg"

# ---------- Helpers ----------


def _wrap_svg(inner: str) -> str:
    return f'<svg xmlns="{SVG_NS}" version="1.1" width="100" height="100">{inner}</svg>'


def _write_svg(tmp_dir: Path, inner_svg: str, name: str = "test.svg") -> Path:
    p = tmp_dir / name
    p.write_text(_wrap_svg(inner_svg), encoding="utf-8")
    return p


def test_empty_file_returns_empty(temp_dir: Path):
    p = temp_dir / "empty.svg"
    p.write_text("", encoding="utf-8")
    assert match_nested_tags(p) == []


def test_missing_file_returns_empty(temp_dir: Path):
    p = temp_dir / "missing.svg"
    assert match_nested_tags(p) == []


def test_malformed_svg_returns_empty(temp_dir: Path):
    p = temp_dir / "bad.svg"
    p.write_text("<svg><text><tspan></svg>", encoding="utf-8")
    assert match_nested_tags(p) == []


def test_no_tspan_returns_empty(temp_dir: Path):
    p = _write_svg(temp_dir, "<text>no tspan here</text>")
    assert match_nested_tags(p) == []


def test_flat_tspans_only_returns_empty(temp_dir: Path):
    p = _write_svg(temp_dir, "<text><tspan>A</tspan><tspan>B</tspan></text>")
    assert match_nested_tags(p) == []


def test_nested_tspan_single_hit(temp_dir: Path):
    p = _write_svg(temp_dir, "<text><tspan>One<tspan>Two</tspan>Three</tspan></text>")
    res = match_nested_tags(p)
    assert len(res) == 1
    assert "<tspan" in res[0]
    assert "One" in res[0] and "Two" in res[0] and "Three" in res[0]


def test_nested_tspan_multiple_hits(temp_dir: Path):
    p = _write_svg(temp_dir, "<text><tspan>X<tspan>Y</tspan></tspan><tspan>P<tspan>Q</tspan></tspan></text>")
    res = match_nested_tags(p)
    assert len(res) == 2
    assert all(r.count("<tspan") >= 2 for r in res)


def test_counts_deeply_nested_levels(temp_dir: Path):
    p = _write_svg(
        temp_dir,
        """<text>
            <tspan>
                a<tspan>
                b<tspan>c</tspan>d
                </tspan>
                e
            </tspan>
        </text>""",
    )
    res = match_nested_tags(p)
    # Only the outermost <tspan> with element children is captured
    assert "a" in res[0] and "b" in res[0] and "c" in res[0] and "d" in res[0] and "e" in res[0]
    assert len(res) == 2


def test_tspan_with_non_element_children_is_ignored(temp_dir: Path):
    # No child elements, only text and tails
    p = _write_svg(temp_dir, "<text><tspan>hello world</tspan></text>")
    assert match_nested_tags(p) == []


def test_namespaced_children_are_counted(temp_dir: Path):
    p = _write_svg(
        temp_dir,
        f"<text><tspan>n<foreignObject xmlns='{SVG_NS}'><tspan>m</tspan></foreignObject></tspan></text>",
    )
    res = match_nested_tags(p)
    assert len(res) == 1
    # serialized string should include foreignObject
    assert "foreignObject" in res[0]


def test_serialization_has_no_backslash_escapes(temp_dir: Path):
    p = _write_svg(temp_dir, '<text><tspan x="10" y="20">A<tspan>B</tspan></tspan></text>')
    s = "".join(match_nested_tags(p))
    assert '\\"' not in s and "\\'" not in s


# ---------- Integration tests: fix then re-check ----------


def test_fix_simple_nested_then_none_left(temp_dir: Path):
    p = _write_svg(temp_dir, "<text><tspan>One<tspan>Two</tspan></tspan></text>")
    before = len(match_nested_tags(p))
    fix_nested_file(p)
    after = len(match_nested_tags(p))
    assert before == 1
    assert after == 0


def test_fix_two_nested_in_same_text_node(temp_dir: Path):
    p = _write_svg(temp_dir, "<text><tspan>A<tspan>B</tspan>C<tspan>D</tspan>E</tspan></text>")
    assert len(match_nested_tags(p)) == 1
    fix_nested_file(p)
    assert match_nested_tags(p) == []
    # Validate content concatenation
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(str(p), parser).getroot()
    t = root.find(f".//{{{SVG_NS}}}tspan")
    assert t is not None and t.text == "ABCDE"


def test_fix_preserves_sibling_tspans_order_and_values(temp_dir: Path):
    p = _write_svg(temp_dir, "<text><tspan>L<tspan>1</tspan></tspan><tspan>L<tspan>2</tspan></tspan></text>")
    fix_nested_file(p)
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(str(p), parser).getroot()
    tspans = root.findall(f".//{{{SVG_NS}}}tspan")
    assert [t.text for t in tspans] == ["L1", "L2"]


def test_fix_keeps_attributes_on_outer_tspan(temp_dir: Path):
    p = _write_svg(temp_dir, '<text><tspan x="10" y="20" class="c">A<tspan>B</tspan></tspan></text>')
    fix_nested_file(p)
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(str(p), parser).getroot()
    t = root.find(f".//{{{SVG_NS}}}tspan")
    assert t.get("x") == "10" and t.get("y") == "20" and t.get("class") == "c"
    assert t.text == "AB"


def test_fix_clears_tail_of_fixed_tspan(temp_dir: Path):
    # After fix, code sets tail=None on the modified tspan
    p = _write_svg(temp_dir, "<text><tspan>A<tspan>B</tspan></tspan>TAIL</text>")
    # Create explicit tail by putting text outside; fix only sets tail for the fixed node
    fix_nested_file(p)
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(str(p), parser).getroot()
    t = root.find(f".//{{{SVG_NS}}}tspan")
    assert t.tail is None


def test_fix_deeply_nested_concatenation_is_linear(temp_dir: Path):
    p = _write_svg(temp_dir, "<text><tspan>0<tspan>1<tspan>2</tspan>3</tspan>4</tspan></text>")
    fix_nested_file(p)
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(str(p), parser).getroot()
    t = root.find(f".//{{{SVG_NS}}}tspan")
    assert t.text == "01234"


def test_fix_does_not_touch_flat_structure(temp_dir: Path):
    p = _write_svg(temp_dir, "<text><tspan>Flat</tspan></text>")
    before = Path.read_text(p, encoding="utf-8")
    fix_nested_file(p, pretty_print=False)
    after = Path.read_text(p, encoding="utf-8")
    # The serializer can change formatting. Compare tree-equivalence instead.
    rb = etree.tostring(etree.fromstring(before.encode("utf-8")), with_tail=False)
    ra = etree.tostring(etree.fromstring(after.encode("utf-8")), with_tail=False)
    assert rb == ra


# ---------- Scenario tests mirrored from real OWID-like snippets ----------


def test_fix_preserves_text_order_with_tails_and_siblings(temp_dir: Path):
    p = _write_svg(temp_dir, "<text><tspan>Start<tspan>Mid</tspan>End</tspan><tspan>Foo</tspan></text>")
    fix_nested_file(p)
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(str(p), parser).getroot()
    t1, t2 = root.findall(f".//{{{SVG_NS}}}tspan")
    assert t1.text == "StartMidEnd"
    assert t2.text == "Foo"


# ---------- Parametrized edge cases ----------


@pytest.mark.parametrize(
    "inner,expected_hits",
    [
        ("<text><tspan/></text>", 0),
        ("<text><tspan> </tspan></text>", 0),
        ("<text><tspan>α<tspan>β</tspan>γ</tspan></text>", 1),
        ("<text><tspan>RTL ‎<tspan>AR</tspan> نص</tspan></text>", 1),
        ('<text><tspan xml:space="preserve">A<tspan> B </tspan>C</tspan></text>', 1),
    ],
)
def test_parametrized_various_patterns(temp_dir: Path, inner: str, expected_hits: int):
    p = _write_svg(temp_dir, inner)
    assert len(match_nested_tags(p)) == expected_hits
    fix_nested_file(p)
    assert len(match_nested_tags(p)) == 0


# ---------- Safety on huge content ----------


def test_handles_large_number_of_tspans(temp_dir: Path):
    # Build many tspans, half nested
    parts = ["<text>"]
    for i in range(100):
        if i % 2 == 0:
            parts.append(f"<tspan>V{i}<tspan>N{i}</tspan></tspan>")
        else:
            parts.append(f"<tspan>V{i}</tspan>")
    parts.append("</text>")
    p = _write_svg(temp_dir, "".join(parts))
    before = len(match_nested_tags(p))
    fix_nested_file(p)
    after = len(match_nested_tags(p))
    assert before == 50
    assert after == 0
