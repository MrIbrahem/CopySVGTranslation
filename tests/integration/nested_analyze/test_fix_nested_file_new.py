from pathlib import Path

import pytest

from CopySVGTranslation.nested_analyze.find_nested_new import fix_nested_file, match_nested_tags

SVG_NS = "http://www.w3.org/2000/svg"

# ---------- Helpers ----------


def _wrap_svg(inner: str) -> str:
    return f'<svg xmlns="{SVG_NS}" version="1.1" width="100" height="100">{inner}</svg>'


def _write_svg(tmp_dir: Path, inner_svg: str, name: str = "test.svg") -> Path:
    p = tmp_dir / name
    p.write_text(_wrap_svg(inner_svg), encoding="utf-8")
    return p


def test_match_and_fix_2(temp_dir: Path):
    text = """
        <g class="markdown-text-wrap">
            <text x="16.0" y="581.0" style="font-size: 13px; line-height: 1.2;">
                <tspan x="16" y="581.0">
                    <tspan style="font-weight: 700;">Data source:</tspan> United Nations Inter-agency Group for Child
                    Mortality Estimation (2025)
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
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="100" height="100">
            <g class="markdown-text-wrap">
                <text x="16.0" y="581.0" style="font-size: 13px; line-height: 1.2;">
                    <tspan style="font-weight: 700;">Data source: </tspan>
                    <tspan>United Nations Inter-agency Group for Child Mortality Estimation (2025)</tspan>
                </text>
            </g>
        </svg>
    """
    new_text_strip = "".join(new_text.split())
    new_text_expected_strip = "".join(new_text_expected.split())

    assert new_text_strip == new_text_expected_strip


@pytest.mark.todo
def test_match_and_fix_to_do(temp_dir: Path):
    text = """
        <g class="markdown-text-wrap">
            <text x="16.0" y="581.0" style="font-size: 13px; line-height: 1.2;">
                <tspan x="16" y="581.0">
                    <tspan style="font-weight: 700;">Data source:</tspan> United Nations Inter-agency Group for Child
                    Mortality Estimation (2025)
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
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="100" height="100">
            <g class="markdown-text-wrap">
                <text x="16.0" y="581.0" style="font-size: 13px; line-height: 1.2;">
                    <tspan style="font-weight: 700;">Data source: </tspan>
                    <tspan>United Nations Inter-agency Group for Child Mortality Estimation (2025)</tspan>
                </text>
            </g>
        </svg>
    """
    new_text_strip = "".join(new_text.split())
    new_text_expected_strip = "".join(new_text_expected.split())

    assert new_text_strip == new_text_expected_strip


def test_match_and_fix_3(temp_dir: Path):
    text = """
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
    """
    p = _write_svg(temp_dir, text, name="testx.svg")
    before = len(match_nested_tags(p))
    fixed = fix_nested_file(p)
    assert fixed is True

    after = len(match_nested_tags(p))
    assert before == 2
    assert after == 0

    new_text = p.read_text(encoding="utf-8")
    new_text_expected = """
        <svg xmlns="http://www.w3.org/2000/svg"
            version="1.1" width="100" height="100">
            <g class="markdown-text-wrap"><text x="10.0" y="94.3"
                    style="font-size: 12.375px; fill: rgb(133, 133, 133); line-height: 1.2;">
                    <tspan style="font-weight: 700;">2.</tspan>
                    <tspan style="font-weight: 700;">Age standardization</tspan>
                    <tspan> Agestandardization is an adjustment that makes it possible to compare populations withdifferent
                        age structures, by </tspan>
                    <tspan x="10" y="109.1">standardizing them to a common reference population.</tspan>
                    <tspan>Read more: </tspan>
                    <tspan href="https://ourworldindata.org/age-standardization" target="_blank" rel="noopener"
                        style="text-decoration: underline;">How does age standardization make health metrics comparable?
                    </tspan>
                </text></g>
        </svg>
    """
    # new_text_strip = "".join([line.strip() for line in new_text.splitlines() if line.strip()])
    # new_text_expected_strip = "".join([line.strip() for line in new_text_expected.splitlines() if line.strip()])

    new_text_strip = "".join(new_text.split())
    new_text_expected_strip = "".join(new_text_expected.split())

    assert new_text_strip == new_text_expected_strip
