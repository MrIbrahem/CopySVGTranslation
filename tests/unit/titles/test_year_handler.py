"""
Unit tests for CopySVGTranslation/titles/year_handler.py module.

Classes to test: YearTitleHandler
"""

from __future__ import annotations

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.core.mapping import TranslationMapping
from CopySVGTranslation.titles.year_handler import YearTitleHandler


# ---------------------------------------------------------------------------
# Static helpers
# ---------------------------------------------------------------------------
class TestMatchYear:
    """Tests for YearTitleHandler.match_year."""

    def test_year_at_end(self):
        assert YearTitleHandler.match_year("COVID-19 pandemic 2020") == "2020"

    def test_year_at_start(self):
        assert YearTitleHandler.match_year("2020 COVID-19 pandemic") == "2020"

    def test_no_year(self):
        assert YearTitleHandler.match_year("No year here") == ""

    def test_short_string(self):
        assert YearTitleHandler.match_year("abc") == ""

    def test_empty_string(self):
        assert YearTitleHandler.match_year("") == ""

    def test_year_only(self):
        assert YearTitleHandler.match_year("2020") == "2020"

    def test_year_with_whitespace(self):
        assert YearTitleHandler.match_year("  2020 report  ") == "2020"

    def test_non_digit_four_chars(self):
        assert YearTitleHandler.match_year("ABCD") == ""


class TestReplaceYearWithPlaceholder:
    """Tests for YearTitleHandler.replace_year_with_placeholder."""

    def test_year_at_end(self):
        result = YearTitleHandler.replace_year_with_placeholder("COVID-19 pandemic 2020", "2020")
        assert result == "COVID-19 pandemic {year}"

    def test_year_at_start(self):
        result = YearTitleHandler.replace_year_with_placeholder("2020 COVID-19 pandemic", "2020")
        assert result == "{year} COVID-19 pandemic"

    def test_year_not_in_expected_position(self):
        result = YearTitleHandler.replace_year_with_placeholder("In 2020 middle", "2020")
        assert result == ""

    def test_whitespace_handling(self):
        result = YearTitleHandler.replace_year_with_placeholder("  text 2020  ", "2020")
        assert result == "text {year}"


class TestApplyYear:
    """Tests for YearTitleHandler.apply_year."""

    def test_basic_replacement(self):
        assert YearTitleHandler.apply_year("pandemic {year}", "2020") == "pandemic 2020"

    def test_multiple_placeholders(self):
        result = YearTitleHandler.apply_year("{year} and {year}", "1999")
        assert result == "1999 and 1999"

    def test_no_placeholder(self):
        assert YearTitleHandler.apply_year("no placeholder", "2020") == "no placeholder"


# ---------------------------------------------------------------------------
# Instance methods
# ---------------------------------------------------------------------------
class TestYearTitleHandlerInit:
    """Tests for YearTitleHandler initialization."""

    def test_default_config(self):
        handler = YearTitleHandler()
        assert handler.enabled is True  # default config has enable_year_titles=True

    def test_disabled_config(self):
        config = TranslationConfig(enable_year_titles=False)
        handler = YearTitleHandler(config)
        assert handler.enabled is False

    def test_custom_config(self):
        config = TranslationConfig(enable_year_titles=True)
        handler = YearTitleHandler(config)
        assert handler.enabled is True


class TestBuildTemplates:
    """Tests for YearTitleHandler.build_templates."""

    def test_disabled_does_nothing(self):
        config = TranslationConfig(enable_year_titles=False)
        handler = YearTitleHandler(config)
        mapping = TranslationMapping(new={"COVID-19 pandemic 2020": {"ar": "جائحة كوفيد 2020"}})
        handler.build_templates(mapping)
        assert mapping.title_new == {}

    def test_builds_title_and_title_new(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping(new={"COVID-19 pandemic 2020": {"ar": "جائحة كوفيد 2020"}})
        handler.build_templates(mapping)
        # title_new should have {year} placeholder
        assert "COVID-19 pandemic {year}" in mapping.title_new

    def test_no_year_entries(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping(new={"No year here": {"ar": "ترجمة"}})
        handler.build_templates(mapping)
        assert mapping.title_new == {}


class TestBuildTemplatesNew:
    """Tests for YearTitleHandler.build_templates."""

    def test_disabled_does_nothing(self):
        config = TranslationConfig(enable_year_titles=False)
        handler = YearTitleHandler(config)
        mapping = TranslationMapping(new={"COVID-19 pandemic 2020": {"ar": "جائحة كوفيد 2020"}})
        handler.build_templates(mapping)
        assert mapping.title_new == {}

    def test_builds_title_new(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping(new={"COVID-19 pandemic 2020": {"ar": "جائحة كوفيد 2020"}})
        handler.build_templates(mapping)
        assert "COVID-19 pandemic {year}" in mapping.title_new
        assert mapping.title_new["COVID-19 pandemic {year}"]["ar"] == "جائحة كوفيد {year}"

    def test_skips_entries_without_year(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping(new={"No year text": {"ar": "ترجمة"}})
        handler.build_templates(mapping)
        assert mapping.title_new == {}

    def test_skips_translation_without_year(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping(new={"Text 2020": {"ar": "بدون سنة"}})

        data = handler.build_title_new_templates(mapping.new, set_key_with_empty_value=False)
        # Translation doesn't end with 2020, so it should be skipped
        assert data == {}

        data1 = handler.build_title_new_templates(mapping.new, set_key_with_empty_value=True)
        assert data1 == {"Text {year}": {}}


class TestExpandForTexts:
    """Tests for YearTitleHandler.expand_for_texts."""

    def test_basic_expansion(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping(title_new={"COVID-19 pandemic {year}": {"ar": "جائحة كوفيد {year}"}})
        result = handler.expand_for_texts(mapping, ["COVID-19 pandemic 1990"])
        assert "COVID-19 pandemic 1990" in result
        assert result["COVID-19 pandemic 1990"]["ar"] == "جائحة كوفيد 1990"

    def test_disabled_returns_empty(self):
        config = TranslationConfig(enable_year_titles=False)
        handler = YearTitleHandler(config)
        mapping = TranslationMapping(title_new={"COVID-19 pandemic {year}": {"ar": "جائحة كوفيد {year}"}})
        result = handler.expand_for_texts(mapping, ["COVID-19 pandemic 1990"])
        assert result == {}

    def test_empty_title_new_returns_empty(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping()
        result = handler.expand_for_texts(mapping, ["COVID-19 pandemic 1990"])
        assert result == {}

    def test_no_matching_template(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping(title_new={"Other title {year}": {"ar": "عنوان {year}"}})
        result = handler.expand_for_texts(mapping, ["COVID-19 pandemic 1990"])
        assert result == {}

    def test_text_without_year(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping(title_new={"COVID-19 pandemic {year}": {"ar": "جائحة كوفيد {year}"}})
        result = handler.expand_for_texts(mapping, ["No year text"])
        assert result == {}

    def test_case_insensitive_lookup(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping(title_new={"covid-19 pandemic {year}": {"ar": "جائحة كوفيد {year}"}})
        result = handler.expand_for_texts(mapping, ["COVID-19 Pandemic 1990"], case_insensitive=True)
        assert "COVID-19 Pandemic 1990" in result

    def test_case_sensitive_no_match(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping(title_new={"covid-19 pandemic {year}": {"ar": "جائحة كوفيد {year}"}})
        result = handler.expand_for_texts(mapping, ["COVID-19 Pandemic 1990"], case_insensitive=False)
        assert result == {}

    def test_multiple_languages(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping(title_new={"pandemic {year}": {"ar": "جائحة {year}", "fr": "pandémie {year}"}})
        result = handler.expand_for_texts(mapping, ["pandemic 2020"])
        assert result["pandemic 2020"]["ar"] == "جائحة 2020"
        assert result["pandemic 2020"]["fr"] == "pandémie 2020"


class TestEnrichMappingForSwitch:
    """Tests for YearTitleHandler.enrich_mapping_for_switch."""

    def test_returns_original_when_no_extra(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping()
        result = handler.enrich_mapping_for_switch(mapping, ["no year text"])
        assert result is mapping

    def test_returns_enriched_mapping(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping(title_new={"pandemic {year}": {"ar": "جائحة {year}"}})
        result = handler.enrich_mapping_for_switch(mapping, ["pandemic 2020"])
        assert result is not mapping
        assert "pandemic 2020" in result.new
        assert result.new["pandemic 2020"]["ar"] == "جائحة 2020"

    def test_does_not_mutate_original(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping(title_new={"pandemic {year}": {"ar": "جائحة {year}"}})
        original_new = dict(mapping.new)
        handler.enrich_mapping_for_switch(mapping, ["pandemic 2020"])
        assert mapping.new == original_new


def make_new_title_translations(
    new: dict[str, dict[str, str]], set_key_with_empty_value: bool = True
) -> dict[str, dict[str, str]]:
    """
    Extract valid title translations by verifying that all translations in a mapping
    end with the same 4-digit year as the key.
    """

    config = TranslationConfig(enable_year_titles=True)
    year_handler = YearTitleHandler(config)
    mapping = TranslationMapping(new=new)

    data = year_handler.build_title_new_templates(mapping.new, set_key_with_empty_value=set_key_with_empty_value)
    if data:
        mapping.title_new.update(data)

    return mapping.title_new


class TestTitlesNew:
    """Test suite for year suffix handling in extract function."""

    def test_basic(self):
        input_data = {"COVID-19 pandemic 2020": {"ar": "جائحة كوفيد 2020", "es": "Pandemia de COVID-19 2020"}}

        result = make_new_title_translations(input_data)

        assert result == {"COVID-19 pandemic {year}": {"ar": "جائحة كوفيد {year}", "es": "Pandemia de COVID-19 {year}"}}

    def test_extract_year_with_multiple_languages(self):
        """Test year suffix handling with multiple languages."""
        input_data = {"Population 2020": {"ar": "السكان 2020", "es": "Population 2020"}}

        result = make_new_title_translations(input_data)

        assert result is not None

        assert result == {"Population {year}": {"ar": "السكان {year}", "es": "Population {year}"}}

    def test_year_in_start_with_multiple_languages(self):
        """Test year suffix handling with multiple languages."""
        input_data = {"2020 Population": {"ar": "السكان 2020", "es": "Population 2020"}}

        result = make_new_title_translations(input_data)

        assert result is not None

        assert result == {"{year} Population": {"ar": "السكان {year}", "es": "Population {year}"}}

    def test_extract_non_year_digits(self):
        """Test that non-year digit sequences are handled correctly."""
        input_data = {"Value 42": {}}

        result = make_new_title_translations(input_data)

        assert result is not None
        assert result == {}

    def test_extract_title(self):
        """Test year suffix handling with multiple languages."""
        input_data = {
            "death rate from malaria, 2000": {
                "ar": "معدل الوفيات الناجمة عن الملاريا، 2000",
                "ko": "2000년 말라리아 사망률",
            }
        }

        result = make_new_title_translations(input_data)

        assert result is not None

        assert result == {
            "death rate from malaria, {year}": {
                "ar": "معدل الوفيات الناجمة عن الملاريا، {year}",
                "ko": "{year}년 말라리아 사망률",
            }
        }

    def test_year_multiple_occurrences(self):
        """Test titles with multiple year occurrences are handled correctly."""
        input_data = {"2020 Highlights of 2020": {"fr": "Faits saillants de 2020 en 2020"}}
        # This test will fail with the current implementation of `replace_year_with_placeholder`,
        # but will pass with the suggested improvement.
        result = make_new_title_translations(input_data)
        expected = {"2020 Highlights of {year}": {"fr": "Faits saillants de 2020 en {year}"}}
        assert result == expected


def get_new_titles_translations(
    all_mappings_title: dict[str, dict[str, str]],
    default_texts: list[str],
) -> dict[str, dict[str, str]]:
    """
    Extract valid title translations by verifying that all translations in a mapping
    end with the same 4-digit year as the key.
    """

    config = TranslationConfig(enable_year_titles=True)
    year_handler = YearTitleHandler(config)

    mapping = TranslationMapping(title_new=all_mappings_title)

    expanded = year_handler.expand_for_texts(
        mapping=mapping,
        default_texts=default_texts,
    )

    return expanded


class TestGetNewTitlesTranslations:
    """Test suite for reattaching year to base titles with {year} template."""

    def test_basic_reconstruction(self):
        all_mappings_title = {
            "COVID-19 pandemic {year}": {"ar": "جائحة كوفيد {year}", "es": "Pandemia de COVID-19 {year}"}
        }
        default_texts = ["COVID-19 pandemic 1990"]
        result = get_new_titles_translations(all_mappings_title, default_texts)
        assert result == {"COVID-19 pandemic 1990": {"ar": "جائحة كوفيد 1990", "es": "Pandemia de COVID-19 1990"}}

    def test_missing_mapping(self):
        all_mappings_title = {"Population {year}": {"ar": "السكان {year}", "es": "Population {year}"}}
        default_texts = ["Unknown 2020"]
        result = get_new_titles_translations(all_mappings_title, default_texts)
        assert result == {}

    def test_invalid_default_text_no_year(self):
        all_mappings_title = {"COVID-19 pandemic {year}": {"ar": "جائحة كوفيد {year}"}}
        default_texts = ["COVID-19 pandemic"]
        result = get_new_titles_translations(all_mappings_title, default_texts)
        assert result == {}

    def test_case_insensitivity(self):
        all_mappings_title = {"covid-19 pandemic {year}": {"ar": "جائحة كوفيد {year}"}}
        default_texts = ["COVID-19 pandemic 2021"]
        result = get_new_titles_translations(all_mappings_title, default_texts)
        assert result == {"COVID-19 pandemic 2021": {"ar": "جائحة كوفيد 2021"}}

    def test_whitespace_handling(self):
        all_mappings_title = {"  covid-19 {year} ": {"ar": "كوفيد {year}"}}
        default_texts = [" COVID-19 2021"]
        result = get_new_titles_translations(all_mappings_title, default_texts)
        assert result == {" COVID-19 2021": {"ar": "كوفيد 2021"}}

    def test_multiple_default_texts(self):
        all_mappings_title = {"pandemic {year}": {"ar": "جائحة {year}", "ko": "{year}년 팬데믹", "fr": ""}}
        default_texts = ["Pandemic 2020", "Unknown 2021", "Pandemic 2022"]
        result = get_new_titles_translations(all_mappings_title, default_texts)
        assert result == {
            "Pandemic 2020": {"ar": "جائحة 2020", "ko": "2020년 팬데믹", "fr": ""},
            "Pandemic 2022": {"ar": "جائحة 2022", "ko": "2022년 팬데믹", "fr": ""},
        }

    def test_multiple_occurrences_of_year(self):
        all_mappings_title = {"pandemic 2020 in {year}": {"ar": "جائحة 2020 {year}"}}
        default_texts = ["Pandemic 2020 in 2020"]
        result = get_new_titles_translations(all_mappings_title, default_texts)
        assert result == {"Pandemic 2020 in 2020": {"ar": "جائحة 2020 2020"}}

    def test_text_too_short(self):
        all_mappings_title = {"{year}": {"en": "{year}"}}
        default_texts = ["2020"]
        result = get_new_titles_translations(all_mappings_title, default_texts)
        assert result == {"2020": {"en": "2020"}}

    def test_text_not_ending_in_digits(self):
        all_mappings_title = {"covid {year}": {"ar": "كوفيد {year}"}}
        default_texts = ["covid year"]
        result = get_new_titles_translations(all_mappings_title, default_texts)
        assert result == {}

    def test_translation_without_year_template(self):
        all_mappings_title = {"covid {year}": {"ar": "كوفيد فقط"}}
        default_texts = ["Covid 2021"]
        result = get_new_titles_translations(all_mappings_title, default_texts)
        assert result == {"Covid 2021": {"ar": "كوفيد فقط"}}


class TestGetNewTitlesTranslationsNew:
    def test_get_new_titles_translations(self):
        new_data = {
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

        title_new = make_new_title_translations(new_data, set_key_with_empty_value=False)
        assert title_new == {}

        title_new1 = make_new_title_translations(new_data, set_key_with_empty_value=True)
        assert title_new1 == {"parkinson's disease prevalence, {year}": {}}
