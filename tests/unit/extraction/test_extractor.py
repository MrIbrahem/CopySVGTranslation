# ruff: noqa: F401
"""
Unit tests for CopySVGTranslation/extraction/extractor.py module.

Functions to test: get_english_default_texts, extract

TODO: write tests
"""


import json
from pathlib import Path

from CopySVGTranslation.extraction.extractor import (
    extract,
    get_english_default_texts,
)

FIXTURES_DIR = Path(__file__).parent.parent.parent


def test_extract_with_string_path() -> None:
    """extract should work with string paths."""
    source_path = str(FIXTURES_DIR / "Parkinsons disease prevalence ihme, World, 1990.svg")

    result = extract(source_path)

    assert result is not None
    assert isinstance(result, dict)
    assert result["new"] == {
        "parkinson's disease prevalence, 1990": {"dag": "Parkinson's doro yɔlibu biɛɣigu ni, yuuni 1990 puli ni"},
        "estimated number of people with parkinson's disease¹ per 100,000 people.": {},
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
        "1. parkinson's disease parkinson's disease is a brain condition that affects movement control. symptoms usually begin gradually and worsen over time,": {},
        "as parts of the brain become progressively damaged over many years.": {},
        "it arises when certain cells in the brain, responsible for producing a chemical called dopamine, become damaged or die. dopamine helps regulate": {},
        "muscle movements, and its deficiency in parkinson's leads to symptoms like tremors (shaking), stiffness, and difficulty with balance and coordination.": {},
        "as the disease progresses, it can also bring about changes in speech, sleep problems, depression, memory difficulties, and fatigue. treatments like": {},
        "medication, devices, and therapies can help manage symptoms and improve quality of life for those with parkinson's.": {},
    }

    assert result["title_new"] == {}
