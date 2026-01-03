# -*- coding: utf-8 -*-

from pathlib import Path
import pytest
from lxml import etree


from CopySVGTranslation.nested_analyze.find_nested_new import match_nested_tags, fix_nested_file

SVG_NS = "http://www.w3.org/2000/svg"

# ---------- Helpers ----------


def _wrap_svg(inner: str) -> str:
    return f'<svg xmlns="{SVG_NS}" version="1.1" width="100" height="100">{inner}</svg>'


def _write_svg(tmp_dir: Path, inner_svg: str, name: str = "test.svg") -> Path:
    p = tmp_dir / name
    p.write_text(_wrap_svg(inner_svg), encoding="utf-8")
    return p

# ---------- Fixtures ----------


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def getSvgFileFromString(temp_dir):
    def _factory(tmp_dir: Path, full_svg: str) -> Path:
        p = tmp_dir / "from_string.svg"
        p.write_text(full_svg, encoding="utf-8")
        return p
    return _factory

# ---------- Core tests: matching behavior ----------


def test_match_and_fix_2(temp_dir: Path):
    text = '''
        <g class="markdown-text-wrap">
            <text x="16.0" y="581.0" style="font-size: 13px; line-height: 1.2;">
                <tspan x="16" y="581.0">
                    <tspan style="font-weight: 700;">Data source:</tspan> United Nations Inter-agency Group for Child
                    Mortality Estimation (2025)
                </tspan>
            </text>
        </g>
    '''
    p = _write_svg(
        temp_dir,
        text,
        name="testx.svg"
    )
    before = len(match_nested_tags(p))
    fixed = fix_nested_file(p)
    assert fixed is True

    after = len(match_nested_tags(p))
    assert before == 1
    assert after == 0

    new_text = p.read_text(encoding="utf-8")
    new_text_expected = '''
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="100" height="100">
            <g class="markdown-text-wrap">
                <text x="16.0" y="581.0" style="font-size: 13px; line-height: 1.2;">
                    <tspan x="16" y="581.0">Data source: United Nations Inter-agency Group for Child Mortality Estimation (2025)</tspan>
                </text>
            </g>
        </svg>
    '''
    new_text_strip = "".join(new_text.split())
    new_text_expected_strip = "".join(new_text_expected.split())

    assert new_text_strip == new_text_expected_strip


@pytest.mark.todo
def test_match_and_fix_to_do(temp_dir: Path):
    text = '''
        <g class="markdown-text-wrap">
            <text x="16.0" y="581.0" style="font-size: 13px; line-height: 1.2;">
                <tspan x="16" y="581.0">
                    <tspan style="font-weight: 700;">Data source:</tspan> United Nations Inter-agency Group for Child
                    Mortality Estimation (2025)
                </tspan>
            </text>
        </g>
    '''
    p = _write_svg(
        temp_dir,
        text,
        name="testx.svg"
    )
    before = len(match_nested_tags(p))
    fixed = fix_nested_file(p)
    assert fixed is True

    after = len(match_nested_tags(p))
    assert before == 1
    assert after == 0

    new_text = p.read_text(encoding="utf-8")
    new_text_expected = '''
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="100" height="100">
            <g class="markdown-text-wrap">
                <text x="16.0" y="581.0" style="font-size: 13px; line-height: 1.2;">
                    <tspan style="font-weight: 700;">Data source: </tspan>
                    <tspan>United Nations Inter-agency Group for Child Mortality Estimation (2025)</tspan>
                </text>
            </g>
        </svg>
    '''
    new_text_strip = "".join(new_text.split())
    new_text_expected_strip = "".join(new_text_expected.split())

    assert new_text_strip == new_text_expected_strip
