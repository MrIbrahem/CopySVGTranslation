import pytest
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySVGTranslation import make_title_translations, get_titles_translations


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


class TestBoth:

    def test_valid_translations(self):
        data = {
            "COVID-19 pandemic 2020": {
                "en": "COVID-19 pandemic 2020",
                "es": "Pandemia de COVID-19 2020",
                "fr": "Pandémie de COVID-19 2020",
            }
        }
        result = make_title_translations(data)
        assert "COVID-19 pandemic" in result
        assert result["COVID-19 pandemic"]["en"] == "COVID-19 pandemic"
        assert result["COVID-19 pandemic"]["es"] == "Pandemia de COVID-19"

    def test_invalid_year_key_skipped(self):
        data = {"InvalidTitle": {"en": "InvalidTitle"}}
        result = make_title_translations(data)
        assert result == {}

    def test_mismatched_years_skipped(self):
        data = {
            "Elections 2021": {"ss": "Lukhetfo lwa-2021", "de": "Elecciones 2020", "es": "Elecciones de 2021"}
        }
        result = make_title_translations(data)
        assert result is not None
        assert isinstance(result, dict)
        assert result == {"Elections": {"ss": "Lukhetfo lwa-", "es": "Elecciones de"}}

    def test_get_titles_translations_basic(self):
        all_mappings = {
            "COVID-19 pandemic": {"en": "COVID-19 pandemic", "es": "Pandemia de COVID-19"}
        }
        default_texts = ["COVID-19 pandemic 2020"]
        result = get_titles_translations(all_mappings, default_texts)
        assert "COVID-19 pandemic 2020" in result
        assert result["COVID-19 pandemic 2020"]["es"] == "Pandemia de COVID-19 2020"

    def test_get_titles_translations_multiple_years(self):
        all_mappings = {
            "Elections": {"ss": "Lukhetfo", "es": "Elecciones"},
            "Pandemic": {"ar": "جائحة", "es": "Pandemia"},
        }
        texts = ["Elections 2019", "Pandemic 2020"]
        result = get_titles_translations(all_mappings, texts)
        assert result["Pandemic 2020"]["es"] == "Pandemia 2020"
        assert result["Pandemic 2020"]["ar"] == "جائحة 2020"
        assert result["Elections 2019"]["ss"] == "Lukhetfo 2019"

    def test_whitespace_handling(self):
        data = {" Event 2023 ": {"en": " Event 2023 ", "ar": " حدث 2023 "}}
        result = make_title_translations(data)
        assert "Event" in result
        assert result["Event"]["ar"] == "حدث"
        assert result == {"Event": {"ar": "حدث", "en": "Event"}}

    def test_empty_input(self):
        assert make_title_translations({}) == {}
        assert get_titles_translations({}, []) == {}

    def test_non_digit_suffix_ignored(self):
        data = {"TitleX": {"en": "TitleX"}}
        result = make_title_translations(data)
        assert result == {}

    def test_combined_workflow(self):
        data = {
            "Olympics 2016 ": {"en": "Olympics 2016", "fr": "Jeux olympiques 2016"},
            " World Cup 2022 ": {"en": "World Cup 2022", "es": "Copa Mundial 2022"},
        }
        extracted = make_title_translations(data)
        texts = ["Olympics 2060", "world Cup 6060"]
        rebuilt = get_titles_translations(extracted, texts)
        assert rebuilt["world Cup 6060"]["es"] == "Copa Mundial 6060"
        assert rebuilt["Olympics 2060"]["fr"] == "Jeux olympiques 2060"
