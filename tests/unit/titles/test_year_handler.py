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
        assert mapping.title == {}
        assert mapping.title_new == {}

    def test_builds_title_and_title_new(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping(new={"COVID-19 pandemic 2020": {"ar": "جائحة كوفيد 2020"}})
        handler.build_templates(mapping)
        # title should have the year stripped
        assert "COVID-19 pandemic" in mapping.title
        # title_new should have {year} placeholder
        assert "COVID-19 pandemic {year}" in mapping.title_new

    def test_no_year_entries(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping(new={"No year here": {"ar": "ترجمة"}})
        handler.build_templates(mapping)
        assert mapping.title == {}
        assert mapping.title_new == {}


class TestBuildTemplatesNew:
    """Tests for YearTitleHandler.build_templates_new."""

    def test_disabled_does_nothing(self):
        config = TranslationConfig(enable_year_titles=False)
        handler = YearTitleHandler(config)
        mapping = TranslationMapping(new={"COVID-19 pandemic 2020": {"ar": "جائحة كوفيد 2020"}})
        handler.build_templates_new(mapping)
        assert mapping.title_new == {}

    def test_builds_title_new(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping(new={"COVID-19 pandemic 2020": {"ar": "جائحة كوفيد 2020"}})
        handler.build_templates_new(mapping)
        assert "COVID-19 pandemic {year}" in mapping.title_new
        assert mapping.title_new["COVID-19 pandemic {year}"]["ar"] == "جائحة كوفيد {year}"

    def test_skips_entries_without_year(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping(new={"No year text": {"ar": "ترجمة"}})
        handler.build_templates_new(mapping)
        assert mapping.title_new == {}

    def test_skips_translation_without_year(self):
        handler = YearTitleHandler()
        mapping = TranslationMapping(new={"Text 2020": {"ar": "بدون سنة"}})
        handler.build_templates_new(mapping)
        # Translation doesn't end with 2020, so it should be skipped
        assert mapping.title_new == {}


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
