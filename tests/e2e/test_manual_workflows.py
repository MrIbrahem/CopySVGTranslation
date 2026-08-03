"""
Pytest conversions of the former manual test scripts:
- tests/manually/extract.py
- tests/manually/inject.py
- tests/manually/nested.py
- tests/manually/titles.py
"""

import json

import pytest

from CopySVGTranslation import extract
from CopySVGTranslation.injection import (
    inject_file_and_save,
)
from CopySVGTranslation.injection.exceptions import (
    SvgNestedTspanExceptionError,
    SvgStructureExceptionError,
)
from CopySVGTranslation.preparation import make_translation_ready
from CopySVGTranslation.titles_workers import get_titles_translations

# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #


def _write_svg(temp_dir, content: str, name: str = "test.svg"):
    """Write *content* to a temporary SVG file and return its Path."""
    svg_file = temp_dir / name
    svg_file.write_text(content, encoding="utf-8")
    return svg_file


# ================================================================== #
# 1. extract.py  –  extraction from a multi-switch SVG
# ================================================================== #


class TestExtractManual:
    """Replaces tests/manually/extract.py."""

    MULTI_SWITCH_SVG = """\
<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
    <switch>
        <text id="t0-ar" systemLanguage="ar">
            <tspan id="t0-ar">الموسيقى في عام 2020</tspan>
        </text>
        <text id="t0-fr" systemLanguage="fr">
            <tspan id="t0-fr">La musique en 2020</tspan>
        </text>
        <text id="t0">
            <tspan id="t0">Music in 2020</tspan>
        </text>
    </switch>
    <switch>
        <text id="t0-ar" systemLanguage="ar">
            <tspan id="t0-ar">مرحبا</tspan>
        </text>
        <text id="t0-fr" systemLanguage="fr">
            <tspan id="t0-fr">Bonjour</tspan>
        </text>
        <text id="t0">
            <tspan id="t0">Hello</tspan>
        </text>
    </switch>
    </svg>"""

    def test_extract_returns_result(self, temp_dir):
        """extract() should return a dict (not None) for a valid multi-switch SVG."""
        svg_file = _write_svg(temp_dir, self.MULTI_SWITCH_SVG)

        tree, root = make_translation_ready(svg_file)
        tree.write(
            str(svg_file),
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
        )

        result = extract(svg_file)

        assert result is not None
        assert isinstance(result, dict)

    def test_extract_detects_default_texts(self, temp_dir):
        """Both default (English) texts should appear under 'new'."""
        svg_file = _write_svg(temp_dir, self.MULTI_SWITCH_SVG)

        tree, root = make_translation_ready(svg_file)
        tree.write(
            str(svg_file),
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
        )

        result = extract(svg_file)
        assert result is not None

        default_texts = set(result["new"].keys())
        assert "music in 2020" in default_texts
        assert "hello" in default_texts

    def test_extract_captures_translations(self, temp_dir):
        """Translations for 'ar' and 'fr' should be captured for each default text."""
        svg_file = _write_svg(temp_dir, self.MULTI_SWITCH_SVG)

        tree, root = make_translation_ready(svg_file)
        tree.write(
            str(svg_file),
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
        )

        result = extract(svg_file)
        assert result is not None

        # "Music in 2020" translations
        music = result["new"]["music in 2020"]
        assert music.get("ar") == "الموسيقى في عام 2020"
        assert music.get("fr") == "La musique en 2020"

        # "Hello" translations
        hello = result["new"]["hello"]
        assert hello.get("ar") == "مرحبا"
        assert hello.get("fr") == "Bonjour"

    def test_extract_no_error(self, temp_dir):
        """The 'error' key should be empty for a well-formed SVG."""
        svg_file = _write_svg(temp_dir, self.MULTI_SWITCH_SVG)

        tree, root = make_translation_ready(svg_file)
        tree.write(
            str(svg_file),
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
        )

        result = extract(svg_file)
        assert result is not None
        assert result["error"] == ""


# ================================================================== #
# 2. inject.py  –  injection with duplicate systemLanguage values
# ================================================================== #


class TestInjectManual:
    """Replaces tests/manually/inject.py.

    The original manual script uses a ``<switch>`` that contains two
    ``<text systemLanguage="la">`` elements.  ``make_translation_ready``
    correctly rejects this as a structure error, so the test asserts
    that the expected exception is raised.
    """

    DUPLICATE_LANG_SVG = """\
<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">\
<switch id="testswitch">\
<text systemLanguage="la">lang la (1)</text>\
<text systemLanguage="la">lang la (2)</text>\
<text>lang none</text>\
</switch></svg>"""

    def test_duplicate_systemlanguage_raises(self, temp_dir):
        """A switch with two <text> sharing the same systemLanguage should raise."""
        svg_file = _write_svg(temp_dir, self.DUPLICATE_LANG_SVG)

        with pytest.raises(SvgStructureExceptionError) as excinfo:
            make_translation_ready(svg_file)

        assert excinfo.value.code == "structure-error-multiple-text-same-lang"

    def test_inject_after_normalization(self, temp_dir):
        """After make_translation_ready, injection should work on a clean SVG."""
        clean_svg = """\
<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">\
<switch id="testswitch">\
<text systemLanguage="la">lang la (1)</text>\
<text>lang none</text>\
</switch></svg>"""
        svg_file = _write_svg(temp_dir, clean_svg)

        data = {"new": {"lang none": {"la": "lang la (new)"}}}

        tree, root = make_translation_ready(svg_file)
        tree.write(
            str(svg_file),
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
        )

        result = inject_file_and_save(
            inject_file=svg_file,
            save_path=svg_file,
            all_mappings=data,
            overwrite=True,
            pretty_print=False,
        )

        # The file should now contain the injected translation
        file_text = svg_file.read_text(encoding="utf-8")
        assert "lang la (new)" in file_text


# ================================================================== #
# 3. nested.py  –  nested <tspan> detection
# ================================================================== #


class TestNestedManual:
    """Replaces tests/manually/nested.py."""

    NESTED_TSPAN_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="850" height="721.1"
    viewBox="0 0 850 721.1"
    style="font-family: Lato, &quot;Helvetica Neue&quot;, Helvetica, Arial, sans-serif;">
    <g id="subtitle" class="markdown-text-wrap">
        <text x="16.0" y="66.5" fill="#5b5b5b"
            style="font-size: 15px; line-height: 1.2;">
            <tspan x="16" y="66.5">Estimated annual number of deaths attributed to <tspan
                    class="dod-span"
                    data-id="obesity">obesity<tspan style="font-feature-settings: &quot;sups&quot;;">
                ¹</tspan>
                </tspan> per 100,000 people.</tspan>
        </text>
    </g>
</svg>"""

    def test_nested_tspan_raises(self, temp_dir):
        """Nested <tspan> elements should trigger SvgNestedTspanExceptionError."""
        svg_file = _write_svg(temp_dir, self.NESTED_TSPAN_SVG)

        with pytest.raises(SvgNestedTspanExceptionError):
            make_translation_ready(svg_file)

    def test_nested_tspan_has_node_info(self, temp_dir):
        """The exception should expose the offending node via .node()."""
        svg_file = _write_svg(temp_dir, self.NESTED_TSPAN_SVG)

        with pytest.raises(SvgNestedTspanExceptionError) as excinfo:
            make_translation_ready(svg_file)

        # The exception carries information about the problematic node
        assert excinfo.value.node() is not None

    def test_nested_tspan_error_code(self, temp_dir):
        """The exception code should indicate nested-tspan unsupported structure."""
        svg_file = _write_svg(temp_dir, self.NESTED_TSPAN_SVG)

        with pytest.raises(SvgNestedTspanExceptionError) as excinfo:
            make_translation_ready(svg_file)

        assert excinfo.value.code == "structure-error-nested-tspans-not-supported"


# ================================================================== #
# 4. titles.py  –  title translation lookup
# ================================================================== #


class TestTitlesManual:
    """Replaces tests/manually/titles.py."""

    INSERT_DATA = {
        "parkinson's disease prevalence,": {
            "pt": "Prevalência de doença de Parkinson,",
            "es": "Prevalencia de la enfermedad de Parkinson,",
            "ca": "Prevalència de la malaltia de Parkinson,",
            "eu": "Parkinsonen gaixotasunaren prebalentzia,",
            "cs": "Prevalence Parkinsonovy nemoci,",
            "si": "පාකින්සන් රෝග ව්‍යාප්තිය,",
            "ar": "انتشار مرض باركنسون،",
        }
    }

    DEFAULT_TEXTS = ["parkinson's disease prevalence, 2028"]

    EXPECTED_LANGS = {"pt", "es", "ca", "eu", "cs", "si", "ar"}

    def test_get_titles_translations_returns_dict(self):
        """get_titles_translations should return a dict."""
        result = get_titles_translations(self.INSERT_DATA, self.DEFAULT_TEXTS)
        assert isinstance(result, dict)

    def test_get_titles_translations_contains_default_text(self):
        """The result should be keyed by the default text (with year)."""
        result = get_titles_translations(self.INSERT_DATA, self.DEFAULT_TEXTS)

        assert "parkinson's disease prevalence, 2028" in result

    def test_get_titles_translations_has_all_languages(self):
        """All 7 languages from insert_data should appear in the result."""
        result = get_titles_translations(self.INSERT_DATA, self.DEFAULT_TEXTS)

        entry = result["parkinson's disease prevalence, 2028"]
        assert set(entry.keys()) == self.EXPECTED_LANGS

    def test_get_titles_translations_values_are_strings(self):
        """Every translation value should be a non-empty string."""
        result = get_titles_translations(self.INSERT_DATA, self.DEFAULT_TEXTS)

        entry = result["parkinson's disease prevalence, 2028"]
        for lang, value in entry.items():
            assert isinstance(value, str), f"{lang} translation is not a string"
            assert len(value) > 0, f"{lang} translation is empty"

    def test_get_titles_translations_json_serializable(self):
        """The result should be JSON-serializable (used downstream as JSON)."""
        result = get_titles_translations(self.INSERT_DATA, self.DEFAULT_TEXTS)

        serialized = json.dumps(result, ensure_ascii=False)
        assert isinstance(serialized, str)
        assert "parkinson's disease prevalence, 2028" in serialized
