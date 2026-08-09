"""
Unit tests for CopySVGTranslation/extraction/extractor.py module.

Classes to test: SVGTranslationExtractor

TODO: write tests
"""

from pathlib import Path

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.extraction.extractor import (
    SVGTranslationExtractor,
)

FULL_TEXT_EXAMPLE = """
<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg">
    <g class="HeaderView" id="header">
        <g id="logo" transform="translate(769, 16) scale(1)">
            <svg xmlns="http://www.w3.org/2000/svg" classname="owidLogo" fill="none" height="36"
                viewBox="0 0 65 36"
                width="65">
                <path fill="#002147" />
                <path fill="#CE261E" />
                <path
                    fill="#fff" />
            </svg>
        </g>
        <a
            href="https://ourworldindata.org/grapher/parkinsons-disease-prevalence-ihme?time=1990&amp;overlay=download-vis"
            id="title"
            style="font-family: &quot;Playfair Display&quot;, Georgia, &quot;Times New Roman&quot;, &quot;Liberation Serif&quot;, serif;">
            <switch>
                <text fill="#2d2e2d" font-size="25.00" font-weight="normal" id="trsvg19-dag"
                    systemLanguage="dag" x="16.0"
                    y="40.3">
                    <tspan id="trsvg1-dag" x="16" y="40.25">Parkinson's doro ni, yuuni 1990 puli ni</tspan>
                </text>
                <text fill="#2d2e2d" font-size="25.00" font-weight="600" id="trsvg19" x="16.0"
                    y="40.3">
                    <tspan id="trsvg1" x="16" y="40.25">Parkinson's disease prevalence, 1990</tspan>
                </text>
            </switch>
        </a>
        <g class="markdown-text-wrap" id="subtitle">
            <switch style="font-size: 15px; line-height: 1.2;">
                <text fill="#5b5b5b" id="trsvg20-dag" style="font-size: 15px; line-height: 1.2;"
                    systemLanguage="dag" x="16.0"
                    y="66.5">
                    <tspan id="trsvg2-dag" x="16" y="66.5">Salo kalinli ban daa mali Parkinson's
                        doro ŋɔ
                        daadam 100,000 kalinli li.</tspan>
                </text>
                <text fill="#5b5b5b" id="trsvg20" style="font-size: 15px; line-height: 1.2;"
                    x="16.0"
                    y="66.5">
                    <tspan id="trsvg2" x="16" y="66.5">Estimated number of people with Parkinson's
                        disease¹
                        per 100,000 people.</tspan>
                </text>
            </switch>
        </g>
    </g>
</svg>
"""


def _write_full_svg(tmp_dir: Path, svg_text: str, name: str = "test.svg") -> Path:
    p = tmp_dir / name
    p.write_text(svg_text.strip(), encoding="utf-8")
    return p


def test_basic_results(temp_dir: Path):

    svg = _write_full_svg(temp_dir, FULL_TEXT_EXAMPLE, name="testx.svg")

    ext = SVGTranslationExtractor()
    result = ext.extract(svg)

    assert result is not None

    # serialized = json.dumps(result.new, ensure_ascii=True)

    assert result.new == {
        "parkinson's disease prevalence, 1990": {"dag": "Parkinson's doro ni, yuuni 1990 puli ni"},
        "estimated number of people with parkinson's disease\u00b9 per 100,000 people.": {
            "dag": "Salo kalinli ban daa mali Parkinson's doro \u014b\u0254 daadam 100,000 kalinli li."
        },
    }


def test_header_result_with_false_config(temp_dir: Path):

    svg = _write_full_svg(temp_dir, FULL_TEXT_EXAMPLE, name="testx.svg")

    ext = SVGTranslationExtractor(config=TranslationConfig(create_lang_template=False))
    result = ext.extract(svg)

    assert result is not None

    # serialized = json.dumps(result.new, ensure_ascii=True)

    assert result.new == {
        "parkinson's disease prevalence, 1990": {"dag": "Parkinson's doro ni, yuuni 1990 puli ni"},
        "estimated number of people with parkinson's disease\u00b9 per 100,000 people.": {
            "dag": "Salo kalinli ban daa mali Parkinson's doro \u014b\u0254 daadam 100,000 kalinli li."
        },
    }

    assert result.meta.get("header") == {
        "parkinson's disease prevalence, 1990": {"dag": "Parkinson's doro ni, yuuni 1990 puli ni"}
    }


def test_header_result_with_true_config(temp_dir: Path):

    svg = _write_full_svg(temp_dir, FULL_TEXT_EXAMPLE, name="testx.svg")

    ext = SVGTranslationExtractor(config=TranslationConfig(create_lang_template=True))
    result = ext.extract(svg)

    assert result is not None

    # serialized = json.dumps(result.new, ensure_ascii=True)

    assert result.new == {
        "parkinson's disease prevalence, 1990": {"dag": "Parkinson's doro ni, yuuni 1990 puli ni"},
        "estimated number of people with parkinson's disease\u00b9 per 100,000 people.": {
            "dag": "Salo kalinli ban daa mali Parkinson's doro \u014b\u0254 daadam 100,000 kalinli li."
        },
        "parkinson's disease prevalence": {
            "dag": "Parkinson's doro ni",
        },
    }

    assert result.meta.get("header") == {
        "parkinson's disease prevalence, 1990": {"dag": "Parkinson's doro ni, yuuni 1990 puli ni"}
    }
