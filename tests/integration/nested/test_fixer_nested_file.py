from pathlib import Path

import pytest
from lxml import etree

from CopySVGTranslation.nested.fixer import MatchFixNestedTags

SVG_NS = "http://www.w3.org/2000/svg"

# ---------- Helpers ----------


def _wrap_svg(inner: str, width: int = 100, height: int = 100) -> str:
    return f'<svg xmlns="{SVG_NS}" version="1.1" width="{width}" height="{height}">{inner}</svg>'


def _write_svg(tmp_dir: Path, inner_svg: str, name: str = "test.svg", width: int = 100, height: int = 100) -> Path:
    p = tmp_dir / name
    p.write_text(_wrap_svg(inner_svg, width, height), encoding="utf-8")
    return p


class TestFixNestedFile:
    def test_empty_file_returns_empty(self, temp_dir: Path):
        p = temp_dir / "empty.svg"
        p.write_text("", encoding="utf-8")

        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        assert matcher.match_nested() == []

    def test_missing_file_returns_empty(self, temp_dir: Path):
        p = temp_dir / "missing.svg"

        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        assert matcher.match_nested() == []

    def test_malformed_svg_returns_empty(self, temp_dir: Path):
        p = temp_dir / "bad.svg"
        p.write_text("<svg><text><tspan></svg>", encoding="utf-8")

        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        assert matcher.match_nested() == []

    def test_no_tspan_returns_empty(self, temp_dir: Path):
        p = _write_svg(temp_dir, "<text>no tspan here</text>")

        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        assert matcher.match_nested() == []

    def test_flat_tspans_only_returns_empty(self, temp_dir: Path):
        p = _write_svg(temp_dir, "<text><tspan>A</tspan><tspan>B</tspan></text>")

        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        assert matcher.match_nested() == []

    def test_nested_tspan_single_hit(self, temp_dir: Path):
        p = _write_svg(temp_dir, "<text><tspan>One<tspan>Two</tspan>Three</tspan></text>")

        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        res = matcher.match_nested()
        assert len(res) == 1
        assert "<tspan" in res[0]
        assert "One" in res[0] and "Two" in res[0] and "Three" in res[0]

    def test_nested_tspan_multiple_hits(self, temp_dir: Path):
        p = _write_svg(temp_dir, "<text><tspan>X<tspan>Y</tspan></tspan><tspan>P<tspan>Q</tspan></tspan></text>")

        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        res = matcher.match_nested()
        assert len(res) == 2
        assert all(r.count("<tspan") >= 2 for r in res)

    def test_counts_deeply_nested_levels(self, temp_dir: Path):
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

        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        res = matcher.match_nested()
        # Every <tspan> that has element children is captured, so the outer and middle tspans both match
        assert "a" in res[0] and "b" in res[0] and "c" in res[0] and "d" in res[0] and "e" in res[0]
        assert len(res) == 2

    def test_tspan_with_non_element_children_is_ignored(self, temp_dir: Path):
        # No child elements, only text and tails
        p = _write_svg(temp_dir, "<text><tspan>hello world</tspan></text>")

        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        assert matcher.match_nested() == []

    def test_namespaced_children_are_counted(self, temp_dir: Path):
        p = _write_svg(
            temp_dir,
            f"<text><tspan>n<foreignObject xmlns='{SVG_NS}'><tspan>m</tspan></foreignObject></tspan></text>",
        )

        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        res = matcher.match_nested()
        assert len(res) == 1
        # serialized string should include foreignObject
        assert "foreignObject" in res[0]

    def test_serialization_has_no_backslash_escapes(self, temp_dir: Path):
        p = _write_svg(temp_dir, '<text><tspan x="10" y="20">A<tspan>B</tspan></tspan></text>')

        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        s = "".join(matcher.match_nested())
        assert '\\"' not in s and "\\'" not in s


# ---------- Integration tests: fix then re-check ----------


class TestFixThenReCheck:

    def test_fix_simple_nested_then_none_left(self, temp_dir: Path):
        p = _write_svg(temp_dir, "<text><tspan>One<tspan>Two</tspan></tspan></text>")
        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        before = len(matcher.match_nested())
        matcher.fix_file()
        after = len(matcher.match_nested())
        assert before == 1
        assert after == 0

    def test_fix_two_nested_in_same_text_node(self, temp_dir: Path):
        p = _write_svg(temp_dir, "<text><tspan>A<tspan>B</tspan>C<tspan>D</tspan>E</tspan></text>")
        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        assert len(matcher.match_nested()) == 1

        matcher.fix_file()
        assert matcher.match_nested() == []
        # Validate content concatenation
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse(str(p), parser).getroot()
        t = root.find(f".//{{{SVG_NS}}}tspan")
        assert t is not None and t.text == "ABCDE"

    def test_fix_preserves_sibling_tspans_order_and_values(self, temp_dir: Path):
        p = _write_svg(temp_dir, "<text><tspan>L<tspan>1</tspan></tspan><tspan>L<tspan>2</tspan></tspan></text>")
        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        matcher.fix_file()
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse(str(p), parser).getroot()
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        assert [t.text for t in tspans] == ["L1", "L2"]

    def test_fix_keeps_attributes_on_outer_tspan(self, temp_dir: Path):
        p = _write_svg(temp_dir, '<text><tspan x="10" y="20" class="c">A<tspan>B</tspan></tspan></text>')
        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        matcher.fix_file()
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse(str(p), parser).getroot()
        t = root.find(f".//{{{SVG_NS}}}tspan")
        assert t is not None
        assert t.get("x") == "10" and t.get("y") == "20" and t.get("class") == "c"
        assert t.text == "AB"

    def test_fix_clears_tail_of_fixed_tspan(self, temp_dir: Path):
        # After fix, code sets tail=None on the modified tspan
        p = _write_svg(temp_dir, "<text><tspan>A<tspan>B</tspan></tspan>TAIL</text>")
        # Create explicit tail by putting text outside; fix only sets tail for the fixed node
        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        matcher.fix_file()
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse(str(p), parser).getroot()
        t = root.find(f".//{{{SVG_NS}}}tspan")
        assert t is not None
        assert t.tail is None

    def test_fix_deeply_nested_concatenation_is_linear(self, temp_dir: Path):
        p = _write_svg(temp_dir, "<text><tspan>0<tspan>1<tspan>2</tspan>3</tspan>4</tspan></text>")
        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        matcher.fix_file()
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse(str(p), parser).getroot()
        t = root.find(f".//{{{SVG_NS}}}tspan")
        assert t is not None
        assert t.text == "01234"

    def test_fix_does_not_touch_flat_structure(self, temp_dir: Path):
        p = _write_svg(temp_dir, "<text><tspan>Flat</tspan></text>")
        matcher = MatchFixNestedTags(p, p, strategy="flatten", pretty_print=False)
        before = Path.read_text(p, encoding="utf-8")

        matcher.fix_file()

        after = Path.read_text(p, encoding="utf-8")
        # The serializer can change formatting. Compare tree-equivalence instead.
        rb = etree.tostring(etree.fromstring(before.encode("utf-8")), with_tail=False)
        ra = etree.tostring(etree.fromstring(after.encode("utf-8")), with_tail=False)
        assert rb == ra


class TestOtherCases:
    # ---------- Scenario tests mirrored from real OWID-like snippets ----------

    def test_fix_preserves_text_order_with_tails_and_siblings(self, temp_dir: Path):
        p = _write_svg(temp_dir, "<text><tspan>Start<tspan>Mid</tspan>End</tspan><tspan>Foo</tspan></text>")
        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        matcher.fix_file()
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
    def test_parametrized_various_patterns(self, temp_dir: Path, inner: str, expected_hits: int):
        p = _write_svg(temp_dir, inner)
        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        assert len(matcher.match_nested()) == expected_hits

        matcher.fix_file()
        assert len(matcher.match_nested()) == 0

    # ---------- Safety on huge content ----------

    def test_handles_large_number_of_tspans(self, temp_dir: Path):
        # Build many tspans, half nested
        parts = ["<text>"]
        for i in range(100):
            if i % 2 == 0:
                parts.append(f"<tspan>V{i}<tspan>N{i}</tspan></tspan>")
            else:
                parts.append(f"<tspan>V{i}</tspan>")
        parts.append("</text>")
        p = _write_svg(temp_dir, "".join(parts))

        matcher = MatchFixNestedTags(p, p, strategy="flatten")

        before = len(matcher.match_nested())

        matcher.fix_file()
        after = len(matcher.match_nested())
        assert before == 50
        assert after == 0
