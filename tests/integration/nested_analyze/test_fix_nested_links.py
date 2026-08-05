from pathlib import Path

import pytest

from CopySVGTranslation.nested import fix_nested_file, match_nested_tags

SVG_NS = "http://www.w3.org/2000/svg"

# ---------- Helpers ----------


def _wrap_svg(inner: str, width: int = 100, height: int = 100) -> str:
    return f'<svg xmlns="{SVG_NS}" version="1.1" width="{width}" height="{height}">{inner}</svg>'


def _write_svg(tmp_dir: Path, inner_svg: str, name: str = "test.svg", width: int = 100, height: int = 100) -> Path:
    p = tmp_dir / name
    p.write_text(_wrap_svg(inner_svg, width, height), encoding="utf-8")
    return p


def _write_full_svg(tmp_dir: Path, svg_text: str, name: str = "test.svg") -> Path:
    p = tmp_dir / name
    p.write_text(svg_text, encoding="utf-8")
    return p


def test_tspan_with_a_link_is_counted_as_nested(temp_dir: Path):
    # NOTE: current implementation flags any element child, not just <tspan>
    p = _write_svg(temp_dir, '<text><tspan>See <a href="https://ex.com">link</a></tspan></text>')
    res = match_nested_tags(p)
    assert len(res) == 1
    assert "<a" in res[0]


def test_match_and_fix_paragraph_with_bold_numbers_and_link(temp_dir: Path):
    p = _write_svg(
        temp_dir,
        """
        <g id="header">
          <text x="10" y="64.6" style="font-size:12px">
            <tspan x="10" y="64.6">
              <tspan style="font-weight:700;">2.</tspan>
              <tspan style="font-weight:700;"> Age standardization</tspan> is used to compare populations by
            </tspan>
            <tspan x="10" y="79.4">standardizing to a common reference.</tspan>
            <tspan x="10" y="94.3">
               Read more:
              <a href="https://ourworldindata.org/age-standardization" target="_blank" rel="noopener" style="text-decoration: underline;">
                How does age standardization make health metrics comparable?
              </a>
            </tspan>
          </text>
        </g>
        """,
    )
    before = len(match_nested_tags(p))
    fix_nested_file(p)
    after = len(match_nested_tags(p))
    # Current matcher flags any element child, so the first and third tspans are hits pre-fix
    assert before == 2
    assert after == 0


def test_match_and_fix_multiple_links_in_different_tspans(temp_dir: Path):
    p = _write_svg(
        temp_dir,
        """
        <text>
          <tspan>Intro <a href="https://a">A</a></tspan>
          <tspan>More <a href="https://b">B</a> text</tspan>
          <tspan>Flat</tspan>
        </text>
        """,
    )
    assert len(match_nested_tags(p)) == 2
    fix_nested_file(p)
    assert len(match_nested_tags(p)) == 0


@pytest.mark.parametrize(
    "inner,expected_hits",
    [
        ('<text><tspan>Has <a href="#">link</a> and <tspan>nested</tspan></tspan></text>', 1),
    ],
)
def test_parametrized_various_patterns(temp_dir: Path, inner: str, expected_hits: int):
    p = _write_svg(temp_dir, inner)
    assert len(match_nested_tags(p)) == expected_hits
    fixed = fix_nested_file(p)
    assert fixed is True
    assert len(match_nested_tags(p)) == 0


def test_match_and_fix(temp_dir: Path):
    text = """
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="900" height="472">
            <g font-family="DejaVu Sans, Arial, Helvetica" stroke-width="1" xml:space="preserve">
                <text id="text3446" x="80" y="120" stroke-width="4">
                    <tspan id="tspan3448" x="80" y="120" font-size="30">
                        <a target="_blank" style="fill: #858585;" href="https://ourworldindata.org/obesity">
                            OurWorldinData.org/obesity
                        </a> | <a target="_blank" style="fill: #858585;" href="https://creativecommons.org/licenses/by/4.0/">
                            CC BY
                        </a>
                    </tspan>
                </text>
            </g>
        </svg>
    """
    p = _write_full_svg(temp_dir, text, name="testx.svg")
    before = len(match_nested_tags(p))
    fixed = fix_nested_file(p)
    assert fixed is True

    after = len(match_nested_tags(p))
    assert before == 1
    assert after == 0

    new_text = p.read_text(encoding="utf-8")
    new_text_expected = """
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="900" height="472">
            <g font-family="DejaVu Sans, Arial, Helvetica" stroke-width="1" xml:space="preserve">
                <text id="text3446" x="80" y="120" stroke-width="4">
                    <tspan id="tspan3448" x="80" y="120" font-size="30">
                            OurWorldinData.org/obesity
                        |
                            CC BY
                    </tspan>
                </text>
            </g>
        </svg>
    """
    new_text_strip = "".join(new_text.split())
    new_text_expected_strip = "".join(new_text_expected.split())

    assert new_text_strip == new_text_expected_strip


def test_match_and_fix_2(temp_dir: Path):
    text = """
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="700" height="300">
        <g class="markdown-text-wrap">
            <text x="10.0" y="94.3" style="font-size: 12.375px; fill: rgb(133, 133, 133); line-height: 1.2;">
            <tspan x="10" y="94.3">
                <tspan style="font-weight: 700;">
                2.
                </tspan>
                                <tspan
                style="font-weight: 700;">
                Age standardization
                </tspan> Age
                standardization is an adjustment that makes it possible to compare populations with
                different age structures, by </tspan>
            <tspan x="10" y="109.1">
                standardizing them to a common reference population.
            </tspan>
            <tspan x="10" y="124.0">Read more: <a href="https://ourworldindata.org/age-standardization"
                target="_blank" rel="noopener"
                style="text-decoration: underline;">
                How does age standardization make health metrics comparable?
                </a>
            </tspan>
            </text>
        </g>
        </svg>

    """
    p = _write_full_svg(temp_dir, text, name="testx.svg")
    before = len(match_nested_tags(p))
    fixed = fix_nested_file(p)
    assert fixed is True

    after = len(match_nested_tags(p))
    assert before == 2
    assert after == 0

    new_text = p.read_text(encoding="utf-8")
    new_text_expected = """
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="700" height="300">
            <g class="markdown-text-wrap">
                <text x="10.0" y="94.3"
                    style="font-size: 12.375px; fill: rgb(133, 133, 133); line-height: 1.2;">
                    <tspan x="10" y="94.3">
                        2. Age standardization Age standardization is an adjustment that
                        makes it possible to compare populations with different age structures, by
                    </tspan>
                    <tspan x="10" y="109.1">
                        standardizing them to a common reference population.
                    </tspan>
                    <tspan x="10" y="124.0">Read more: How does age standardization make health metrics
                        comparable?</tspan>
                </text>
            </g>
        </svg>

    """
    # new_text_strip = "".join([line.strip() for line in new_text.splitlines() if line.strip()])
    # new_text_expected_strip = "".join([line.strip() for line in new_text_expected.splitlines() if line.strip()])

    new_text_strip = "".join(new_text.split())
    new_text_expected_strip = "".join(new_text_expected.split())

    assert new_text_strip == new_text_expected_strip


def test_match_and_fix_3(temp_dir: Path):
    text = """
        <g class="markdown-text-wrap">
            <text x="10.0" y="94.3" style="font-size: 12.375px; fill: rgb(133, 133, 133); line-height: 1.2;">
                <tspan x="10" y="124.0">
                    Read more: <a href="https://ourworldindata.org/age-standardization" target="_blank" rel="noopener" style="text-decoration: underline;">
                    How does age standardization make health metrics comparable?
                    </a>
                </tspan>
            </text>
        </g>

    """
    p = _write_svg(temp_dir, text, name="testx.svg")
    before = len(match_nested_tags(p))
    fixed = fix_nested_file(p)
    assert fixed is True

    after = len(match_nested_tags(p))
    assert before == 1
    assert after == 0

    new_text = p.read_text(encoding="utf-8")
    new_text_expected = """
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="100" height="100"><g class="markdown-text-wrap"><text x="10.0" y="94.3" style="font-size: 12.375px; fill: rgb(133, 133, 133); line-height: 1.2;"><tspan x="10" y="124.0">Read more:How does age standardization make health metrics comparable?</tspan></text></g></svg>
    """
    new_text_strip = "".join([line.strip() for line in new_text.splitlines() if line.strip()])
    new_text_expected_strip = "".join([line.strip() for line in new_text_expected.splitlines() if line.strip()])

    assert new_text_strip == new_text_expected_strip
