"""
Pytest conversions of the former manual test scripts:
- tests/manually/extract.py
- tests/manually/inject.py
- tests/manually/nested.py
- tests/manually/titles.py
"""

from pathlib import Path

import pytest
from lxml import etree

from CopySVGTranslation import TranslationConfig
from CopySVGTranslation.exceptions import (
    SvgNestedTspanError,
    SvgStructureError,
)
from CopySVGTranslation.legacy.extract import extract
from CopySVGTranslation.legacy import (
    inject_file_tree,
)
from CopySVGTranslation.preparation import SvgPreparationPipeline

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


def preparer_run(source_file: Path | str) -> tuple[etree._ElementTree, etree._Element]:
    """
    Legacy function-style wrapper around SvgPreparationPipeline, kept for
    backward compatibility with existing callers.
    """
    config = TranslationConfig(
        nested_strategy="raise",
    )
    preparer = SvgPreparationPipeline(config)
    return preparer.run(path=source_file)


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

        tree, root = preparer_run(svg_file)
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

        tree, root = preparer_run(svg_file)
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

        tree, root = preparer_run(svg_file)
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

        tree, root = preparer_run(svg_file)
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
    ``<text systemLanguage="la">`` elements.  ``preparer_run``
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

        with pytest.raises(SvgStructureError) as excinfo:
            preparer_run(svg_file)

        assert excinfo.value.code == "structure-error-multiple-text-same-lang"

    def test_inject_after_normalization(self, temp_dir):
        """After preparer_run, injection should work on a clean SVG."""
        clean_svg = """\
<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">\
<switch id="testswitch">\
<text systemLanguage="la">lang la (1)</text>\
<text>lang none</text>\
</switch></svg>"""
        svg_file = _write_svg(temp_dir, clean_svg)

        data = {"new": {"lang none": {"la": "lang la (new)"}}}

        tree, root = preparer_run(svg_file)
        tree.write(
            str(svg_file),
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
        )

        result = inject_file_tree(
            inject_file=svg_file,
            save_path=svg_file,
            mapping=data,
            overwrite=True,
            pretty_print=False,
            save_result=True,
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
        """Nested <tspan> elements should trigger SvgNestedTspanError."""
        svg_file = _write_svg(temp_dir, self.NESTED_TSPAN_SVG)

        with pytest.raises(SvgNestedTspanError):
            preparer_run(svg_file)

    def test_nested_tspan_error_code(self, temp_dir):
        """The exception code should indicate nested-tspan unsupported structure."""
        svg_file = _write_svg(temp_dir, self.NESTED_TSPAN_SVG)

        with pytest.raises(SvgNestedTspanError) as excinfo:
            preparer_run(svg_file)

        assert excinfo.value.code == "structure-error-nested-tspans-not-supported"
