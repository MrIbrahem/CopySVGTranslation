import pytest
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySvgTranslate import make_title_translations, get_titles_translations


class TestMakeTitlesTranslations:

    def test_make_title_translations(self):
        data = {
            "parkinson's disease prevalence, 1990": {
                "pt": "Prevalência de doença de Parkinson, 1990",
                "es": "Prevalencia de la enfermedad de Parkinson, 1990",
                "ca": "Prevalència de la malaltia de Parkinson, 1990",
                "eu": "Parkinsonen gaixotasunaren prebalentzia, 1990",
                "cs": "Prevalence Parkinsonovy nemoci, 1990",
                "si": "පාකින්සන් රෝග ව්‍යාප්තිය, 1990",
                "ar": "انتشار مرض باركنسون، 1990"
            }
        }
        expected = {
            "parkinson's disease prevalence,": {
                "pt": "Prevalência de doença de Parkinson,",
                "es": "Prevalencia de la enfermedad de Parkinson,",
                "ca": "Prevalència de la malaltia de Parkinson,",
                "eu": "Parkinsonen gaixotasunaren prebalentzia,",
                "cs": "Prevalence Parkinsonovy nemoci,",
                "si": "පාකින්සන් රෝග ව්‍යාප්තිය,",
                "ar": "انتشار مرض باركنسون،"
            }
        }
        title_translations = make_title_translations(data)

        assert title_translations is not None
        assert isinstance(title_translations, dict)
        assert title_translations == expected

    def test_make_title_translations_one_bad(self):
        data = {
            "parkinson's disease prevalence, 1990": {
                "pt": "Prevalência de doença de Parkinson, 1990",
                "es": "Prevalencia de la enfermedad de Parkinson, 1990",
                "ca": "Prevalència de la malaltia de Parkinson",
                "eu": "Parkinsonen gaixotasunaren prebalentzia, 1990",
                "cs": "Prevalence Parkinsonovy nemoci, 1990",
                "si": "පාකින්සන් රෝග ව්‍යාප්තිය, 1990",
                "ar": "انتشار مرض باركنسون، 1990"
            }
        }
        expected = {
            "parkinson's disease prevalence,": {
                "pt": "Prevalência de doença de Parkinson,",
                "es": "Prevalencia de la enfermedad de Parkinson,",
                # "ca": "Prevalència de la malaltia de Parkinson,",
                "eu": "Parkinsonen gaixotasunaren prebalentzia,",
                "cs": "Prevalence Parkinsonovy nemoci,",
                "si": "පාකින්සන් රෝග ව්‍යාප්තිය,",
                "ar": "انتشار مرض باركنسون،"
            }
        }
        title_translations = make_title_translations(data)

        assert title_translations is not None
        assert isinstance(title_translations, dict)
        assert title_translations == expected


class TestGetTitlesTranslations:

    def test_get_titles_translations(self):
        insert_data = {
            "parkinson's disease prevalence,": {
                "pt": "Prevalência de doença de Parkinson,",
                "es": "Prevalencia de la enfermedad de Parkinson,",
                "ca": "Prevalència de la malaltia de Parkinson,",
                "eu": "Parkinsonen gaixotasunaren prebalentzia,",
                "cs": "Prevalence Parkinsonovy nemoci,",
                "si": "පාකින්සන් රෝග ව්‍යාප්තිය,",
                "ar": "انتشار مرض باركنسون،"
            }
        }
        default_texts = [
            "Parkinson's disease prevalence, 2028"
        ]

        expected_data = {
            "Parkinson's disease prevalence, 2028": {
                "pt": "Prevalência de doença de Parkinson, 2028",
                "es": "Prevalencia de la enfermedad de Parkinson, 2028",
                "ca": "Prevalència de la malaltia de Parkinson, 2028",
                "eu": "Parkinsonen gaixotasunaren prebalentzia, 2028",
                "cs": "Prevalence Parkinsonovy nemoci, 2028",
                "si": "පාකින්සන් රෝග ව්‍යාප්තිය, 2028",
                "ar": "انتشار مرض باركنسون، 2028"
            }
        }

        result = get_titles_translations(insert_data, default_texts)

        assert result is not None
        assert isinstance(result, dict)
        assert result == expected_data

    def test_get_titles_translations_not_matched(self):
        insert_data = {
            "parkinson's disease prevalence ,": {
                "pt": "Prevalência de doença de Parkinson,",
                "es": "Prevalencia de la enfermedad de Parkinson,",
                "ca": "Prevalència de la malaltia de Parkinson,",
                "eu": "Parkinsonen gaixotasunaren prebalentzia,",
                "cs": "Prevalence Parkinsonovy nemoci,",
                "si": "පාකින්සන් රෝග ව්‍යාප්තිය,",
                "ar": "انتشار مرض باركنسون،"
            }
        }
        default_texts = [
            "parkinson's disease prevalence, 2028"
        ]

        result = get_titles_translations(insert_data, default_texts)

        assert result is not None
        assert isinstance(result, dict)
        assert result == {}
