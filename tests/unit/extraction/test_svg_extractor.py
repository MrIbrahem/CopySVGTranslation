"""
Unit tests for CopySVGTranslation/extraction/extractor.py module.

Functions to test: extract
"""


from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.extraction.extractor import SVGTranslationExtractor

TSPANS_BY_ID_DATA = {
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

NEW_DATA = {
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

def test_extract_svg_with_string_path(fixtures_dir) -> None:
    """extract should work with string paths."""
    source_path = str(fixtures_dir / "Parkinsons disease prevalence ihme, World, 1990.svg")

    service = SVGTranslationExtractor(TranslationConfig(set_key_with_empty_value=False))

    _result = service.extract(source_path)
    result = _result.to_json()

    assert result["tspans_by_id"] == TSPANS_BY_ID_DATA
    assert result["new"] == NEW_DATA

    assert result["title_new"] == {}

def test_extract_svg_with_string_path_2(fixtures_dir) -> None:
    """extract should work with string paths."""
    source_path = str(fixtures_dir / "Parkinsons disease prevalence ihme, World, 1990.svg")

    # test with set_key_with_empty_value=True
    service2 = SVGTranslationExtractor(TranslationConfig(set_key_with_empty_value=True))

    result2 = service2.extract(source_path).to_json()

    assert result2["title_new"] == {"parkinson's disease prevalence, {year}": {}}
