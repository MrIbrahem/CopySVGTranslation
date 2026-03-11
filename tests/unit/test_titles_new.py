"""
"""

import unittest

from CopySVGTranslation.titles_new import make_new_title_translations, get_new_titles_translations


class TestExtractYearHandling(unittest.TestCase):
    """Test suite for year suffix handling in extract function."""

    def test_basic(self):
        input_data = {
            "COVID-19 pandemic 2020": {"ar": "جائحة كوفيد 2020", "es": "Pandemia de COVID-19 2020"}
        }

        result = make_new_title_translations(input_data)

        assert result == {"COVID-19 pandemic {year}": {"ar": "جائحة كوفيد {year}", "es": "Pandemia de COVID-19 {year}"}}

    def test_extract_year_with_multiple_languages(self):
        """Test year suffix handling with multiple languages."""
        input_data = {
            "Population 2020": {"ar": "السكان 2020", "es": "Population 2020"}
        }

        result = make_new_title_translations(input_data)

        self.assertIsNotNone(result)

        assert result == {'Population {year}': {'ar': 'السكان {year}', 'es': 'Population {year}'}}

    def test_extract_non_year_digits(self):
        """Test that non-year digit sequences are handled correctly."""
        input_data = {
            "Value 42": {}
        }

        result = make_new_title_translations(input_data)

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

        result = make_new_title_translations(input_data)

        self.assertIsNotNone(result)

        assert result == {
            'death rate from malaria, {year}': {
                'ar': 'معدل الوفيات الناجمة عن الملاريا، {year}',
                'ko': '{year}년 말라리아 사망률',
            }
        }


if __name__ == '__main__':
    unittest.main()
