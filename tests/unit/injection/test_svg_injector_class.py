"""
Unit tests for SVGTranslationInjector class, InjectorData, and InjectorStats.
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.injection.injector import SVGTranslationInjector
from CopySVGTranslation.result import InjectorData, InjectorStats

SVG_NS = "http://www.w3.org/2000/svg"
SVG_NSMAP = {"svg": SVG_NS}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _wrap_svg(inner: str) -> str:
    return f'<svg xmlns="{SVG_NS}" version="1.1">{inner}</svg>'


def _write_svg(tmp_path: Path, inner: str, name: str = "test.svg") -> Path:
    p = tmp_path / name
    p.write_text(_wrap_svg(inner), encoding="utf-8")
    return p


def _count_lang_nodes(root: etree._Element, lang: str) -> int:
    """Count <text systemLanguage="lang"> nodes (namespace-aware)."""
    return len(root.xpath(f'.//svg:text[@systemLanguage="{lang}"]', namespaces=SVG_NSMAP))


def _get_ar_text(root: etree._Element) -> str | None:
    """Return text content of the first Arabic tspan (namespace-aware)."""
    tspans = root.xpath('//svg:text[@systemLanguage="ar"]/svg:tspan', namespaces=SVG_NSMAP)
    return tspans[0].text if tspans else None


def _get_default_texts(root: etree._Element) -> list[str]:
    """Return tspan text content of default (no systemLanguage) text nodes."""
    tspans = root.xpath("//svg:text[not(@systemLanguage)]/svg:tspan/text()", namespaces=SVG_NSMAP)
    return tspans


# ===========================================================================
# InjectorStats dataclass tests
# ===========================================================================

class TestSetup:
    def tostring(self, el: etree._Element, pretty_print=False) -> str:
        return etree.tostring(el, pretty_print=pretty_print).decode("utf-8").strip()

    def normalize(self, file_text):
        # return file_text.strip()
        return " ".join([x.strip() for x in file_text.strip().splitlines()])


class TestInjectorStats(TestSetup):
    """Tests for the InjectorStats dataclass."""

    def test_default_values(self):
        stats = InjectorStats()
        assert stats.all_languages == 0
        assert stats.new_languages == 0
        assert stats.processed_switches == 0
        assert stats.inserted_translations == 0
        assert stats.skipped_translations == 0
        assert stats.updated_translations == 0
        assert stats.languages_before == []
        assert stats.languages_after == []
        assert stats.error == ""

    def test_to_json_returns_dict(self):
        stats = InjectorStats()
        result = stats.to_json()
        assert isinstance(result, dict)
        expected_keys = {
            "all_languages",
            "new_languages",
            "processed_switches",
            "inserted_translations",
            "skipped_translations",
            "updated_translations",
            "languages_before",
            "languages_after",
            "error",
        }
        assert set(result.keys()) == expected_keys

    def test_to_json_reflects_values(self):
        stats = InjectorStats()
        stats._update(
            all_languages=3,
            new_languages=2,
            inserted_translations=5,
            error="",
        )
        result = stats.to_json()
        assert result["all_languages"] == 3
        assert result["new_languages"] == 2
        assert result["inserted_translations"] == 5

    def test_fields_are_independent(self):
        a = InjectorStats()
        b = InjectorStats()
        a.languages_before.append("ar")
        assert b.languages_before == []


# ===========================================================================
# InjectorData dataclass tests
# ===========================================================================


class TestInjectorData(TestSetup):
    """Tests for the InjectorData dataclass."""

    def test_default_values(self):
        data = InjectorData()
        assert data.tree is None
        assert isinstance(data.inject_stats, InjectorStats)

    def test_to_json_structure(self):
        data = InjectorData()
        result = data.to_json()
        assert isinstance(result, dict)
        assert "tree" in result
        assert "inject_stats" in result
        assert "error" in result

    def test_to_json_error_from_stats(self):
        data = InjectorData()
        data.inject_stats.error = "Something broke"
        result = data.to_json()
        assert result["error"] == "Something broke"


# ===========================================================================
# SVGTranslationInjector constructor tests
# ===========================================================================


class TestSVGTranslationInjectorInit(TestSetup):
    """Tests for SVGTranslationInjector initialization."""

    def test_default_parameters(self):
        config = TranslationConfig()
        inj = SVGTranslationInjector(config)
        assert inj.config.case_insensitive is True
        assert inj.config.overwrite is False
        assert inj.config.pretty_print is None

    def test_custom_parameters(self):
        config = TranslationConfig(
            case_insensitive=False,
            overwrite=True,
            pretty_print=False,
        )
        inj = SVGTranslationInjector(config)
        assert inj.config.case_insensitive is False
        assert inj.config.overwrite is True
        assert inj.config.pretty_print is False


# ===========================================================================
# SVGTranslationInjector.inject() — basic insertion
# ===========================================================================


class TestSVGTranslationInjectorBasic(TestSetup):
    """Tests for the inject() method — basic insertion scenarios."""

    def test_inject_single_language(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        inj = SVGTranslationInjector()
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        result = inj.inject(svg_path=svg, mapping=mappings)

        assert isinstance(result, InjectorData)
        assert result.tree is not None
        assert result.inject_stats.error == ""
        assert result.inject_stats.inserted_translations == 1

    def test_inject_multiple_languages(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        inj = SVGTranslationInjector()
        mappings = {"new": {"hello": {"ar": "مرحبا", "fr": "Bonjour"}}}

        result = inj.inject(svg_path=svg, mapping=mappings)

        assert result.inject_stats.inserted_translations == 2
        assert result.inject_stats.all_languages == 2

    def test_inject_multiple_switches(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
            <switch>
                <text id="t1"><tspan id="t1">Goodbye</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        inj = SVGTranslationInjector()
        mappings = {"new": {"hello": {"ar": "مرحبا"}, "goodbye": {"ar": "وداعا"}}}

        result = inj.inject(svg_path=svg, mapping=mappings)

        assert result.inject_stats.processed_switches == 2
        assert result.inject_stats.inserted_translations == 2

    def test_inject_preserves_existing_text(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        inj = SVGTranslationInjector()
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        result = inj.inject(svg_path=svg, mapping=mappings)
        assert result is not None
        assert result.tree is not None

        root = result.tree.getroot()
        default_texts = _get_default_texts(root)
        assert "Hello" in default_texts


# ===========================================================================
# Case sensitivity tests
# ===========================================================================


class TestSVGTranslationInjectorCaseSensitivity(TestSetup):
    """Tests for case-insensitive and case-sensitive matching."""

    def test_case_insensitive_match(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0"><tspan id="t0">Hello World</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        config = TranslationConfig(case_insensitive=True)
        inj = SVGTranslationInjector(config)
        # Key is lowercase; source text is mixed case
        mappings = {"new": {"hello world": {"ar": "مرحبا بالعالم"}}}

        result = inj.inject(svg_path=svg, mapping=mappings)
        assert result.inject_stats.inserted_translations == 1

    def test_case_sensitive_no_match(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0"><tspan id="t0">Hello World</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        config = TranslationConfig(case_insensitive=False)
        inj = SVGTranslationInjector(config)
        # Key is lowercase; source text is mixed case — should NOT match
        mappings = {"new": {"hello world": {"ar": "مرحبا بالعالم"}}}

        result = inj.inject(svg_path=svg, mapping=mappings)
        assert result.inject_stats.inserted_translations == 0

    def test_case_sensitive_exact_match(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0"><tspan id="t0">Hello World</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        config = TranslationConfig(case_insensitive=False)
        inj = SVGTranslationInjector(config)
        mappings = {"new": {"Hello World": {"ar": "مرحبا بالعالم"}}}

        result = inj.inject(svg_path=svg, mapping=mappings)
        assert result.inject_stats.inserted_translations == 1


# ===========================================================================
# Overwrite mode tests
# ===========================================================================


class TestSVGTranslationInjectorOverwrite(TestSetup):
    """Tests for overwrite behaviour."""

    def test_skip_existing_language_without_overwrite(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">Old</tspan></text>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        config = TranslationConfig(overwrite=False)
        inj = SVGTranslationInjector(config)
        mappings = {"new": {"hello": {"ar": "New"}}}

        result = inj.inject(svg_path=svg, mapping=mappings)

        assert result.inject_stats.skipped_translations == 1
        assert result.inject_stats.updated_translations == 0

    def test_overwrite_existing_language(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">Old</tspan></text>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        config = TranslationConfig(overwrite=True)
        inj = SVGTranslationInjector(config)
        mappings = {"new": {"hello": {"ar": "New"}}}

        result = inj.inject(svg_path=svg, mapping=mappings)

        assert result.inject_stats.updated_translations == 1
        assert result.inject_stats.skipped_translations == 0

    def test_overwrite_updates_text_content(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">Old Arabic</tspan></text>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        config = TranslationConfig(overwrite=True)
        inj = SVGTranslationInjector(config)
        mappings = {"new": {"hello": {"ar": "New Arabic"}}}

        result = inj.inject(svg_path=svg, mapping=mappings)
        assert result is not None
        assert result.tree is not None

        root = result.tree.getroot()

        ar_text = _get_ar_text(root)
        assert ar_text == "New Arabic"

    def test_mixed_insert_and_skip(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">Existing</tspan></text>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        config = TranslationConfig(overwrite=False)
        inj = SVGTranslationInjector(config)
        mappings = {"new": {"hello": {"ar": "Should skip", "fr": "Should insert"}}}

        result = inj.inject(svg_path=svg, mapping=mappings)

        assert result.inject_stats.skipped_translations == 1
        assert result.inject_stats.inserted_translations == 1


# ===========================================================================
# Save result tests
# ===========================================================================


class TestSVGTranslationInjectorSave(TestSetup):
    """Tests for saving the injection result to disk."""

    def test_save_result_writes_file(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        target = tmp_path / "output.svg"
        inj = SVGTranslationInjector()
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        result = inj.inject(
            svg_path=svg,
            mapping=mappings,
            save_path=target,
            save=True,
        )

        assert target.exists()
        assert result.tree is not None

    def test_save_result_false_does_not_write(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        target = tmp_path / "output.svg"
        inj = SVGTranslationInjector()
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        inj.inject(
            svg_path=svg,
            mapping=mappings,
            save_path=target,
            save=False,
        )

        assert not target.exists()

    def test_save_result_without_target_returns_error(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        inj = SVGTranslationInjector()
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        result = inj.inject(
            svg_path=svg,
            mapping=mappings,
            save=True,
            save_path=None,
        )

        assert result.inject_stats.error != ""

    def test_saved_file_is_valid_xml(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        target = tmp_path / "output.svg"
        inj = SVGTranslationInjector()
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        inj.inject(
            svg_path=svg,
            mapping=mappings,
            save_path=target,
            save=True,
        )

        # Should parse without error
        tree = etree.parse(str(target))
        root = tree.getroot()
        assert root.tag == "{http://www.w3.org/2000/svg}svg"


# ===========================================================================
# Language tracking tests
# ===========================================================================


class TestSVGTranslationInjectorLanguageTracking(TestSetup):
    """Tests for before/after language statistics."""

    def test_languages_before_empty(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        inj = SVGTranslationInjector()
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        result = inj.inject(svg_path=svg, mapping=mappings)

        assert result.inject_stats.languages_before == []

    def test_new_languages_counted(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        inj = SVGTranslationInjector()
        mappings = {"new": {"hello": {"ar": "مرحبا", "fr": "Bonjour"}}}

        result = inj.inject(svg_path=svg, mapping=mappings)

        assert result.inject_stats.new_languages == 2
        assert sorted(result.inject_stats.languages_after) == ["ar", "fr"]

    def test_existing_languages_tracked(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0-es" systemLanguage="es"><tspan id="t0-es">Hola</tspan></text>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        inj = SVGTranslationInjector()
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        result = inj.inject(svg_path=svg, mapping=mappings)

        assert "es" in result.inject_stats.languages_before
        assert result.inject_stats.all_languages == 2  # es + ar


# ===========================================================================
# Error handling tests
# ===========================================================================


class TestSVGTranslationInjectorErrors(TestSetup):
    """Tests for error handling in SVGTranslationInjector."""

    def test_nonexistent_file(self, tmp_path: Path):
        inj = SVGTranslationInjector()
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        result = inj.inject(svg_path=tmp_path / "missing.svg", mapping=mappings)

        assert result.inject_stats.error == "File does not exist"
        assert result.tree is None

    def test_no_mappings(self, tmp_path: Path):
        svg = _write_svg(tmp_path, '<switch><text id="t0"><tspan>Hi</tspan></text></switch>')
        inj = SVGTranslationInjector()

        result = inj.inject(svg_path=svg, mapping=None)

        assert result.inject_stats.error == "No valid mappings found"
        assert result.tree is None

    def test_empty_mappings(self, tmp_path: Path):
        svg = _write_svg(tmp_path, '<switch><text id="t0"><tspan>Hi</tspan></text></switch>')
        inj = SVGTranslationInjector()

        result = inj.inject(svg_path=svg, mapping={})

        assert result.inject_stats.error == "No valid mappings found"

    def test_invalid_xml(self, tmp_path: Path):
        svg = tmp_path / "bad.svg"
        svg.write_text("<svg><unclosed>", encoding="utf-8")
        inj = SVGTranslationInjector()
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        result = inj.inject(svg_path=svg, mapping=mappings)

        assert result.inject_stats.error != ""
        assert result.tree is None


# ===========================================================================
# work_on_switches unit tests (direct calls)
# ===========================================================================


class TestWorkOnSwitches(TestSetup):
    """Direct unit tests for work_on_switches without file I/O."""

    def _make_root(self, inner: str) -> etree._Element:
        return etree.fromstring(_wrap_svg(inner))

    def test_inserts_translation_nodes(self):
        root = self._make_root(
            """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        )
        inj = SVGTranslationInjector()
        existing_ids = set(root.xpath("//@id"))

        inj.work_on_switches(root, mapping={"new": {"hello": {"ar": "مرحبا"}}}, existing_ids=existing_ids)

        ar_nodes = root.xpath('.//svg:text[@systemLanguage="ar"]', namespaces=SVG_NSMAP)
        assert len(ar_nodes) == 1

    def test_generates_unique_ids(self):
        root = self._make_root(
            """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        )
        inj = SVGTranslationInjector()
        existing_ids = set(root.xpath("//@id"))

        inj.work_on_switches(
            root,
            mapping={"new": {"hello": {"ar": "مرحبا", "fr": "Bonjour"}}},
            existing_ids=existing_ids,
        )

        ar_id = root.xpath('.//svg:text[@systemLanguage="ar"]/@id', namespaces=SVG_NSMAP)[0]
        fr_id = root.xpath('.//svg:text[@systemLanguage="fr"]/@id', namespaces=SVG_NSMAP)[0]
        assert ar_id != fr_id
        assert ar_id.startswith("t0")
        assert fr_id.startswith("t0")

    def test_newly_generated_ids_are_unique(self):
        root = self._make_root(
            """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        )
        inj = SVGTranslationInjector()
        existing_ids = set(root.xpath("//@id"))

        inj.work_on_switches(
            root,
            mapping={"new": {"hello": {"ar": "مرحبا"}}},
            existing_ids=existing_ids,
        )

        # Collect only the newly added <text> nodes (those with systemLanguage)
        new_text_ids = root.xpath(".//svg:text[@systemLanguage]/@id", namespaces=SVG_NSMAP)
        new_tspan_ids = root.xpath(".//svg:text[@systemLanguage]/svg:tspan/@id", namespaces=SVG_NSMAP)

        # Newly generated IDs should not collide with the original IDs
        for new_id in list(new_text_ids) + list(new_tspan_ids):
            assert new_id not in {"t0"}, f"New ID '{new_id}' collides with existing ID"

        # Newly generated text and tspan IDs should differ from each other
        all_new = list(new_text_ids) + list(new_tspan_ids)
        assert len(all_new) == len(set(all_new))

    def test_no_match_skips_switch(self):
        root = self._make_root(
            """
            <switch>
                <text id="t0"><tspan id="t0">Goodbye</tspan></text>
            </switch>
        """
        )
        inj = SVGTranslationInjector()

        stats = inj.work_on_switches(root, mapping={"new": {"hello": {"ar": "مرحبا"}}})

        # No new nodes should be added
        ar_nodes = root.xpath('.//svg:text[@systemLanguage="ar"]', namespaces=SVG_NSMAP)
        assert len(ar_nodes) == 0
        assert stats.processed_switches == 1


# ===========================================================================
# End-to-end: extract then inject via classes
# ===========================================================================


class TestExtractorInjectorE2E(TestSetup):
    """End-to-end tests using SVGTranslationExtractor and SVGTranslationInjector together."""

    def test_extract_then_inject(self, tmp_path: Path):
        from CopySVGTranslation.extraction.extractor import SVGTranslationExtractor

        # Source SVG with translations
        source_inner = """
            <switch>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">hi</tspan></text>
                <text id="t0-fr" systemLanguage="fr"><tspan id="t0-fr">Bonjour</tspan></text>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
            <switch>
                <text id="t1-ar" systemLanguage="ar"><tspan id="t1-ar">by</tspan></text>
                <text id="t1"><tspan id="t1">Goodbye</tspan></text>
            </switch>
        """
        source_svg = _write_svg(tmp_path, source_inner, name="source.svg")

        # Target SVG without translations
        target_inner = """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
            <switch>
                <text id="t1"><tspan id="t1">Goodbye</tspan></text>
            </switch>
        """
        target_svg = _write_svg(tmp_path, target_inner, name="target.svg")
        output_svg = tmp_path / "output.svg"

        # Extract
        extractor = SVGTranslationExtractor()
        extract_result = extractor.extract(source_svg)
        assert extract_result.error == ""

        # Inject
        injector = SVGTranslationInjector()
        inject_result = injector.inject(
            svg_path=target_svg,
            mapping=extract_result.to_json(),
            save_path=output_svg,
            save=True,
        )

        assert inject_result.tree is not None
        assert inject_result.inject_stats.error == ""
        assert inject_result.inject_stats.languages_before == []
        assert inject_result.inject_stats.languages_after == ["ar", "fr"]

        assert output_svg.exists()

        # Verify output (text/tspan elements stay in SVG namespace)
        tree = etree.parse(str(output_svg))
        root = tree.getroot()

        new_text = self.tostring(root)
        assert '/>' not in new_text

        new_text_expected = """
            <svg xmlns="http://www.w3.org/2000/svg" version="1.1">
                <switch>
                    <text id="t0">
                        <tspan id="t0">Hello</tspan>
                    </text>
                    <text id="t0-ar" systemLanguage="ar">
                        <tspan id="t0-ar_1">hi</tspan>
                    </text>
                    <text id="t0-fr" systemLanguage="fr">
                        <tspan id="t0-fr_1">Bonjour</tspan>
                    </text>
                </switch>
                <switch>
                    <text id="t1">
                        <tspan id="t1">Goodbye</tspan>
                    </text>
                    <text id="t1-ar" systemLanguage="ar">
                        <tspan id="t1-ar_1">by</tspan>
                    </text>
                </switch>
            </svg>
        """
        assert self.normalize(new_text) == self.normalize(new_text_expected)

        assert len(root.xpath('.//svg:text[@systemLanguage="ar"]', namespaces=SVG_NSMAP)) == 2
        assert len(root.xpath('.//svg:text[@systemLanguage="fr"]', namespaces=SVG_NSMAP)) == 1

        assert inject_result.inject_stats.inserted_translations == 3  # ar + fr for Hello, ar for Goodbye


    def test_extract_inject_preserves_content(self, tmp_path: Path):
        from CopySVGTranslation.extraction.extractor import SVGTranslationExtractor

        source_inner = """
            <switch>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">ترجمة دقيقة</tspan></text>
                <text id="t0"><tspan id="t0">Exact translation</tspan></text>
            </switch>
        """
        source_svg = _write_svg(tmp_path, source_inner, name="source.svg")

        target_inner = """
            <switch>
                <text id="t0"><tspan id="t0">Exact translation</tspan></text>
            </switch>
        """
        target_svg = _write_svg(tmp_path, target_inner, name="target.svg")
        output_svg = tmp_path / "output.svg"

        extractor = SVGTranslationExtractor()
        data = extractor.extract(source_svg).to_json()

        injector = SVGTranslationInjector()
        result = injector.inject(
            svg_path=target_svg,
            mapping=data,
            save_path=output_svg,
            save=True,
        )

        tree = etree.parse(str(output_svg))
        root = tree.getroot()
        ar_text = root.xpath('.//svg:text[@systemLanguage="ar"]/svg:tspan/text()', namespaces=SVG_NSMAP)[0]
        assert ar_text == "ترجمة دقيقة"
