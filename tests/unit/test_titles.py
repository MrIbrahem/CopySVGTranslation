"""
"""

import unittest

from CopySVGTranslation.titles import make_title_translations, get_titles_translations


class TestExtractYearHandling(unittest.TestCase):
    """Test suite for year suffix handling in extract function."""

    def test_basic(self):
        input_data = {
            "COVID-19 pandemic 2020": {"ar": "جائحة كوفيد 2020", "es": "Pandemia de COVID-19 2020"}
        }

        result = make_title_translations(input_data)

        assert result == {"COVID-19 pandemic": {"ar": "جائحة كوفيد", "es": "Pandemia de COVID-19"}}

    def test_extract_year_with_multiple_languages(self):
        """Test year suffix handling with multiple languages."""
        input_data = {
            "Population 2020": {"ar": "السكان 2020", "es": "Population 2020"}
        }

        result = make_title_translations(input_data)

        self.assertIsNotNone(result)

        assert result == {'Population': {'ar': 'السكان', 'es': 'Population'}}

    def test_extract_non_year_digits(self):
        """Test that non-year digit sequences are handled correctly."""
        input_data = {
            "Value 42": {}
        }

        result = make_title_translations(input_data)

        self.assertIsNotNone(result)
        assert result == {}

    def test_extract_title(self):
        """Test year suffix handling with multiple languages."""
        input_data = {
            "death rate from malaria, 2000": {
                "ar": "معدل الوفيات الناجمة عن الملاريا، 2000",
                "ko": "2000년 말라리아 사망률"
            }
        }

        result = make_title_translations(input_data)

        self.assertIsNotNone(result)

        assert result == {
            'death rate from malaria,': {
                'ar': 'معدل الوفيات الناجمة عن الملاريا،'
            }
        }


class TestGetTitlesTranslations(unittest.TestCase):
    """Test suite for reattaching year to base titles."""

    def test_basic_reconstruction(self):
        all_mappings_title = {
            "COVID-19 pandemic": {"ar": "جائحة كوفيد", "es": "Pandemia de COVID-19"}
        }
        default_texts = ["COVID-19 pandemic 1990"]
        result = get_titles_translations(all_mappings_title, default_texts)
        self.assertEqual(
            result,
            {
                "COVID-19 pandemic 1990": {
                    "ar": "جائحة كوفيد 1990",
                    "es": "Pandemia de COVID-19 1990"
                }
            }
        )

    def test_missing_mapping(self):
        all_mappings_title = {
            "Population": {"ar": "السكان", "es": "Population"}
        }
        default_texts = ["Unknown 2020"]
        result = get_titles_translations(all_mappings_title, default_texts)
        self.assertEqual(result, {})

    def test_invalid_default_text_no_year(self):
        all_mappings_title = {
            "COVID-19 pandemic": {"ar": "جائحة كوفيد"}
        }
        default_texts = ["COVID-19 pandemic"]
        result = get_titles_translations(all_mappings_title, default_texts)
        self.assertEqual(result, {})

    def test_case_insensitivity(self):
        all_mappings_title = {
            "coviD-19 PANdemic": {"ar": "جائحة كوفيد"}
        }
        default_texts = ["COVID-19 pandemic 2021"]
        result = get_titles_translations(all_mappings_title, default_texts)
        self.assertEqual(result, {"COVID-19 pandemic 2021": {"ar": "جائحة كوفيد 2021"}})

    def test_whitespace_handling(self):
        all_mappings_title = {
            "  COVID-19 pandemic  ": {"ar": "جائحة كوفيد"}
        }
        default_texts = ["  COVID-19 pandemic 2021"]
        result = get_titles_translations(all_mappings_title, default_texts)
        self.assertEqual(result, {"  COVID-19 pandemic 2021": {"ar": "جائحة كوفيد 2021"}})

    def test_multiple_default_texts(self):
        all_mappings_title = {
            "pandemic": {"ar": "جائحة"}
        }
        default_texts = ["Pandemic 2020", "Unknown 2021", "Pandemic 2022"]
        result = get_titles_translations(all_mappings_title, default_texts)
        self.assertEqual(
            result,
            {
                "Pandemic 2020": {"ar": "جائحة 2020"},
                "Pandemic 2022": {"ar": "جائحة 2022"}
            }
        )

    def test_text_too_short(self):
        all_mappings_title = {
            "": {"en": "empty"}
        }
        default_texts = ["2020"]
        result = get_titles_translations(all_mappings_title, default_texts)
        self.assertEqual(result, {})

    def test_text_not_ending_in_digits(self):
        all_mappings_title = {
            "covid": {"ar": "كوفيد"}
        }
        default_texts = ["covid year"]
        result = get_titles_translations(all_mappings_title, default_texts)
        self.assertEqual(result, {})


if __name__ == '__main__':
    unittest.main()
