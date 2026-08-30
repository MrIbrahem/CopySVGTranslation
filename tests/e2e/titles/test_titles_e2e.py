"""
Extended comprehensive unit tests for CopySVGTranslation covering additional edge cases
and previously untested functions.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from CopySVGTranslation import SVGTranslationService


class TestExtractYearHandling:
    """Test suite for year suffix handling in extract function."""

    @pytest.fixture(autouse=True)
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.service = SVGTranslationService()

        yield
        """Clean up test fixtures."""
        # Clean up temporary files
        shutil.rmtree(self.test_dir)

    def test_extract_detects_year_suffix(self):
        """Test extraction detects and handles year suffixes."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1-ar" systemLanguage="ar"><tspan id="t1-ar">السكان 2020</tspan></text>
                <text id="text1"><tspan id="t1">Population 2020</tspan></text>
            </switch>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        _result = self.service.extract(svg_path)
        assert _result.success
        assert _result.data is not None
        result = _result.data.to_json()

        # Should create title mapping for year-suffixed text
        assert isinstance(result["title_new"], dict)

        assert "title_new" in result
        assert result["title_new"] == {"population {year}": {"ar": "السكان {year}"}}

    def test_extract_year_with_multiple_languages(self):
        """Test year suffix handling with multiple languages."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1-ar" systemLanguage="ar"><tspan id="t1-ar">السكان 2020</tspan></text>
                <text id="text1-fr" systemLanguage="fr"><tspan id="t1-fr">Population 2020</tspan></text>
                <text id="text1"><tspan id="t1">Population 2020</tspan></text>
            </switch>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        _result = self.service.extract(svg_path)
        assert _result.success
        assert _result.data is not None
        result = _result.data.to_json()

        assert result is not None
        assert "new" in result

        assert "title_new" in result
        assert result["title_new"] == {
            "population {year}": {
                "ar": "السكان {year}",
                "fr": "Population {year}",
            }
        }

    def test_extract_non_year_digits(self):
        """Test that non-year digit sequences are handled correctly."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1"><tspan id="t1">Value 42</tspan></text>
            </switch>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        _result = self.service.extract(svg_path)
        assert _result.success
        assert _result.data is not None
        result = _result.data.to_json()

        assert result is not None
        assert result == {
            "new": {"value 42": {}},
            "title_new": {},
            "meta": {},
            "tspans_by_id": {"t1": "Value 42"},
            "error": "",
        }

    def test_extract_title_new(self):
        """Test year suffix handling with multiple languages."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1-ko" systemLanguage="ko"><tspan id="t1-ko">2000년 말라리아 사망률</tspan></text>
                <text id="text1-ar" systemLanguage="ar"><tspan id="t1-ar">معدل الوفيات الناجمة عن الملاريا، 2000</tspan></text>
                <text id="text1"><tspan id="t1">death rate from malaria, 2000</tspan></text>
            </switch>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        _result = self.service.extract(svg_path)
        assert _result.success
        assert _result.data is not None
        result = _result.data.to_json()

        assert result is not None
        assert "new" in result

        assert "title_new" in result
        assert result["title_new"] == {
            "death rate from malaria, {year}": {
                "ko": "{year}년 말라리아 사망률",
                "ar": "معدل الوفيات الناجمة عن الملاريا، {year}",
            }
        }
