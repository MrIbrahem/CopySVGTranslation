# -*- coding: utf-8 -*-

from pathlib import Path
import pytest
from CopySVGTranslation.nested_analyze.find_nested import match_nested_tags, fix_nested_file

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


def test_tspan_with_a_link_is_counted_as_nested(temp_dir: Path):
    # NOTE: current implementation flags any element child, not just <tspan>
    p = _write_svg(
        temp_dir,
        '<text><tspan>See <a href="https://ex.com">link</a></tspan></text>'
    )
    res = match_nested_tags(p)
    assert len(res) == 1
    assert "<a" in res[0]


def test_match_and_fix_paragraph_with_bold_numbers_and_link(temp_dir: Path):
    p = _write_svg(
        temp_dir,
        '''
        <g id="header">
          <text x="10" y="64.6" style="font-size:12px">
            <tspan x="10" y="64.6">
              <tspan style="font-weight:700;">2.</tspan>
              <tspan style="font-weight:700;"> Age standardization</tspan> is used to compare populations by
            </tspan>
            <tspan x="10" y="79.4">standardizing to a common reference.</tspan>
            <tspan x="10" y="94.3">
              📄 Read more:
              <a href="https://ourworldindata.org/age-standardization" target="_blank" rel="noopener" style="text-decoration: underline;">
                How does age standardization make health metrics comparable?
              </a>
            </tspan>
          </text>
        </g>
        '''
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
        '''
        <text>
          <tspan>Intro <a href="https://a">A</a></tspan>
          <tspan>More <a href="https://b">B</a> text</tspan>
          <tspan>Flat</tspan>
        </text>
        '''
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
    fix_nested_file(p)
    assert len(match_nested_tags(p)) == 0
