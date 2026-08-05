"""
Unit tests for CopySVGTranslation/extraction/extractor.py module.

Functions to test: extract
"""

from pathlib import Path

import pytest

from CopySVGTranslation.extraction.extractor import SVGTranslationExtractor  # noqa: F401
from CopySVGTranslation.legacy.extract import extract

SVG_NS = "http://www.w3.org/2000/svg"


def _wrap_svg(inner: str, width: int = 100, height: int = 100) -> str:
    return f'<svg xmlns="{SVG_NS}" version="1.1" width="{width}" height="{height}">{inner}</svg>'


def _write_svg(tmp_dir: Path, inner_svg: str, name: str = "test.svg", width: int = 100, height: int = 100) -> Path:
    p = tmp_dir / name
    p.write_text(_wrap_svg(inner_svg, width, height), encoding="utf-8")
    return p


@pytest.mark.todo
def test_match_header_tags(temp_dir: Path):
    text = """
        <g class="HeaderView" id="header">
            <a href="https://ourworldindata.org/grapher/parkinsons-disease-prevalence-ihme?time=1990&amp;overlay=download-vis"
                id="title"
                style="font-family: &quot;Playfair Display&quot;, Georgia, &quot;Times New Roman&quot;, &quot;Liberation Serif&quot;, serif;">
                <switch>
                <text fill="#2d2e2d" font-size="25.00" font-weight="normal" id="trsvg19-dag" systemLanguage="dag" x="16.0"
                    y="40.3">
                    <tspan id="trsvg1-dag" x="16" y="40.25">Parkinson's doro yɔlibu biɛɣigu ni, yuuni 1990
                    puli ni</tspan>
                </text>
                <text fill="#2d2e2d" font-size="25.00" font-weight="600" id="trsvg19" x="16.0" y="40.3">
                    <tspan id="trsvg1" x="16" y="40.25">Parkinson's disease prevalence, 1990</tspan>
                </text>
                </switch>
            </a>
            <g class="markdown-text-wrap" id="subtitle">
                <switch style="font-size: 15px; line-height: 1.2;">
                <text fill="#5b5b5b" id="trsvg20-dag" style="font-size: 15px; line-height: 1.2;" systemLanguage="dag" x="16.0"
                    y="66.5">
                    <tspan id="trsvg2-dag" x="16" y="66.5">Salo kalinli ban daa mali Parkinson's doro ŋɔ
                    daadam 100,000 kalinli li.</tspan>
                </text>
                <text fill="#5b5b5b" id="trsvg20" style="font-size: 15px; line-height: 1.2;" x="16.0" y="66.5">
                    <tspan id="trsvg2" x="16" y="66.5">Estimated number of people with Parkinson's disease¹
                    per 100,000 people.</tspan>
                </text>
                </switch>
            </g>
        </g>
    """

    file = _write_svg(temp_dir, text, name="testx.svg")
    assert file is not None


def test_extract_with_string_path_zz(fixtures_dir) -> None:
    """extract should work with string paths."""
    source_path = str(fixtures_dir / "Parkinsons disease prevalence ihme, World, 1990.svg")

    result = extract(source_path)

    assert result is not None
    assert isinstance(result, dict)

    assert result["tspans_by_id"] == {
        "trsvg1": "Parkinson's disease prevalence, 1990",
        "trsvg2": "Estimated number of people with Parkinson's disease¹\n            per 100,000 people.",
        "trsvg3": "No data",
        "trsvg4": "0",
        "trsvg5": "50",
        "trsvg6": "100",
        "trsvg7": "150",
        "trsvg8": "200",
        "trsvg9": "250",
        "trsvg10": "300",
        "trsvg11": "Data source: IHME, Global Burden of Disease (2025)",
        "trsvg12": "OurWorldinData.org/causes-of-death | CC BY",
        "trsvg13": "1. Parkinson's disease Parkinson's disease is a brain\n            condition that affects movement control. Symptoms usually begin gradually and worsen\n            over time,",
        "trsvg14": "as parts of the brain become progressively damaged over\n            many years.",
        "trsvg15": "It arises when certain cells in the brain, responsible\n            for producing a chemical called dopamine, become damaged or die. Dopamine helps regulate",
        "trsvg16": "muscle movements, and its deficiency in Parkinson's\n            leads to symptoms like tremors (shaking), stiffness, and difficulty with balance and\n            coordination.",
        "trsvg17": "As the disease progresses, it can also bring about\n            changes in speech, sleep problems, depression, memory difficulties, and fatigue.\n            Treatments like",
        "trsvg18": "medication, devices, and therapies can help manage\n            symptoms and improve quality of life for those with Parkinson's.",
    }

    assert result["new"] == {
        "parkinson's disease prevalence, 1990": {"dag": "Parkinson's doro yɔlibu biɛɣigu ni, yuuni 1990 puli ni"},
        "estimated number of people with parkinson's disease¹ per 100,000 people.": {
            "dag": "Salo kalinli ban daa mali Parkinson's doro ŋɔ daadam 100,000 kalinli li."
        },
        "no data": {"dag": "Lahabali kani"},
        "0": {},
        "50": {"dag": "50"},
        "100": {"dag": "100"},
        "150": {"dag": "150"},
        "200": {"dag": "200"},
        "250": {"dag": "250"},
        "300": {"dag": "300"},
        "data source: ihme, global burden of disease (2025)": {
            "dag": "Lahabali ni yina shɛli: IHME, Global Burden of Disease ( yuuni2025)"
        },
        "ourworldindata.org/causes-of-death | cc by": {"dag": "OurWorldinData.org/causes-of-death | CC BY"},
        "1. parkinson's disease parkinson's disease is a brain condition that affects movement control. symptoms usually begin gradually and worsen over time,": {
            "dag": "Parkinson's doro ŋɔ nyɛla zuɣupuri ni doro din damdi daadam chandi. Di nahingbana tooi piligiri baalim hali n ti mali ti kpe yɔɣu saha shɛli."
        },
        "as parts of the brain become progressively damaged over many years.": {
            "dag": "Pirimla zuɣupuri maa damya yuun gbaliŋ."
        },
        "it arises when certain cells in the brain, responsible for producing a chemical called dopamine, become damaged or die. dopamine helps regulate": {
            "dag": "Di piligirimi saha shɛli zuɣupuri binnɛma ban su' ni bɛ mali kɛmikal din yuli booni dopamine la, yi deei daŋa beei n kpi. Dopamine ŋɔ nyɛla din maani"
        },
        "muscle movements, and its deficiency in parkinson's leads to symptoms like tremors (shaking), stiffness, and difficulty with balance and coordination.": {
            "dag": "Niŋgbuŋ dambu bee chandi, ka di filimbu Parkinson's doro ŋɔ ni zaŋsim nahingbana kamani niŋgbuŋ sɔɣibu bee kpaŋbu bee ka niri lahi ka yiko o maŋa dambu polo."
        },
        "as the disease progresses, it can also bring about changes in speech, sleep problems, depression, memory difficulties, and fatigue. treatments like": {
            "dag": "Doro ŋɔ yi kpɛei yɔɣu din tooi taɣi niri yeltoɣa bee o gom bee n tooi suhisaɣingu bee ka o tamdi yɛla bee ka wumsim mali o saha kam. Tibbu soya kamani"
        },
        "medication, devices, and therapies can help manage symptoms and improve quality of life for those with parkinson's.": {
            "dag": "Tilahi valibu bee zahimbu kpatuɣa mini tibbu soya din pahi nyɛla din tooi soŋsim baligi doro ŋɔ nahingbana ka kpaŋsi alaafee biɛɣigu n ti niro ŋun mali Parkinson's doro ŋɔ."
        },
    }

    assert result["title_new"] == {}
