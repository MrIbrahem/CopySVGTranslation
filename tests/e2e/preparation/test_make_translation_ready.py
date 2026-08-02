"""

pytest tests/preparation/test_preparation.py

"""

from pathlib import Path

from CopySVGTranslation.injection.preparation import make_translation_ready, normalize_lang

FIXTURES_DIR = Path(__file__).parent


class TestIntegrationWorkflows:

    def test_make_translation_ready(self, tmp_path):
        svg_new = tmp_path / "before_translate_ready.svg"
        tree, _root = make_translation_ready(FIXTURES_DIR / "before_translate.svg", write_back=False)
        tree.write(str(svg_new), pretty_print=True, xml_declaration=True, encoding="utf-8")
        assert svg_new.exists()
        assert tree.getroot().tag.endswith("svg")


class TestPreparationFunctions:
    """Tests for SVG preparation utility functions."""

    def test_normalize_lang_simple_codes(self):
        """Test normalizing simple language codes."""
        assert normalize_lang("en") == "en"
        assert normalize_lang("AR") == "ar"
        assert normalize_lang("FR") == "fr"

    def test_normalize_lang_with_region_codes(self):
        """Test normalizing language codes with regions."""
        assert normalize_lang("en_US") == "en-US"
        assert normalize_lang("en-GB") == "en-GB"
        assert normalize_lang("zh_CN") == "zh-CN"

    def test_normalize_lang_complex_codes(self):
        """Test normalizing complex language codes."""
        assert normalize_lang("en_US_POSIX") == "en-US-Posix"
