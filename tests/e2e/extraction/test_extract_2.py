import pytest

from CopySVGTranslation import TranslationConfig, TranslationMapping
from CopySVGTranslation.service import SVGTranslationService


class TestExtractor:
    """Test cases for extraction functions."""

    @pytest.fixture(autouse=True)
    def setup(self):
        config = TranslationConfig()
        self.service = SVGTranslationService(config)

    def test_extract_with_no_tspan_ids(self, temp_dir):
        """Test extraction with multiple languages."""
        svg = temp_dir / "test.svg"
        svg.write_text(
            """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="t0-ar" systemLanguage="ar">
                    <tspan>مرحبا</tspan>
                </text>
                <text id="t0-fr" systemLanguage="fr">
                    <tspan>Bonjour</tspan>
                </text>
                <text id="t0">
                    <tspan>Hello</tspan>
                </text>
            </switch>
            </svg>""",
            encoding="utf-8",
        )
        _result = self.service.extract(svg)

        assert isinstance(_result.data, TranslationMapping)
        result = _result.data.to_json()

        assert result is not None
        assert "new" in result
        assert result == {"new": {"hello": {}}, "tspans_by_id": {}, "title_new": {}, "meta": {}, "error": ""}
        # assert "ar" in result["new"]["hello"]
        # assert "fr" in result["new"]["hello"]

    def test_extract_with_span_and_text_ids(self, temp_dir):
        """Test extraction with multiple languages."""
        svg = temp_dir / "test.svg"
        svg.write_text(
            """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="t0-ar" systemLanguage="ar">
                    <tspan id="t0-ar">مرحبا</tspan>
                </text>
                <text id="t0-fr" systemLanguage="fr">
                    <tspan id="t0-fr" >Bonjour</tspan>
                </text>
                <text id="t0">
                    <tspan id="t0">Hello</tspan>
                </text>
            </switch>
            </svg>""",
            encoding="utf-8",
        )
        _result = self.service.extract(svg)

        assert isinstance(_result.data, TranslationMapping)
        result = _result.data.to_json()

        assert result is not None
        assert "new" in result
        assert "ar" in result["new"]["hello"]
        assert "fr" in result["new"]["hello"]
        assert result == {
            "new": {"hello": {"ar": "مرحبا", "fr": "Bonjour"}},
            "tspans_by_id": {"t0": "Hello"},
            "title_new": {},
            "error": "",
            "meta": {},
        }
