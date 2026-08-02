"""
Regression tests for bug fixes identified in the codebase audit.

Each test class corresponds to a specific bug and verifies that the fix
prevents the previously broken behavior.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest
from lxml import etree

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SVG_NS = "http://www.w3.org/2000/svg"
SVG_NSMAP = {"svg": SVG_NS}


def _wrap_svg(inner: str) -> str:
    return f'<?xml version="1.0" encoding="utf-8"?><svg xmlns="{SVG_NS}" version="1.1">{inner}</svg>'


def _write_svg(tmp_path: Path, inner: str, name: str = "test.svg") -> Path:
    p = tmp_path / name
    p.write_text(_wrap_svg(inner), encoding="utf-8")
    return p


# ===========================================================================
# BUG-01: Injector accumulates state across calls
# ===========================================================================


class TestInjectorStateIsolation:
    """Verify that SVGTranslationInjector does not leak state between calls."""

    def test_stats_do_not_accumulate_across_calls(self, tmp_path: Path):
        """Calling inject() twice should produce independent stats, not accumulated ones."""
        from CopySVGTranslation.injection.svg_injector import SVGTranslationInjector

        inner = '<switch><text id="t0"><tspan id="t0">Hello</tspan></text></switch>'
        svg = _write_svg(tmp_path, inner)
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        inj = SVGTranslationInjector()

        r1 = inj.inject(inject_file=svg, all_mappings=mappings)
        first_inserted = r1.new_stats.inserted_translations
        first_processed = r1.new_stats.processed_switches

        r2 = inj.inject(inject_file=svg, all_mappings=mappings)
        second_inserted = r2.new_stats.inserted_translations
        second_processed = r2.new_stats.processed_switches

        # Each call should insert 1 translation and process 1 switch
        assert first_inserted == 1
        assert first_processed == 1
        assert second_inserted == 1, "Stats accumulated: second call should insert 1, not more"
        assert second_processed == 1, "Stats accumulated: second call should process 1, not more"

    def test_returned_objects_are_independent(self, tmp_path: Path):
        """Each inject() call should return a fresh InjectorData object."""
        from CopySVGTranslation.injection.svg_injector import SVGTranslationInjector

        inner = '<switch><text id="t0"><tspan id="t0">Hello</tspan></text></switch>'
        svg = _write_svg(tmp_path, inner)
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        inj = SVGTranslationInjector()

        r1 = inj.inject(inject_file=svg, all_mappings=mappings)
        r2 = inj.inject(inject_file=svg, all_mappings=mappings)

        assert r1 is not r2, "inject() should return different InjectorData objects"
        assert r1.new_stats is not r2.new_stats, "Stats objects should be independent"

    def test_error_does_not_persist_after_successful_call(self, tmp_path: Path):
        """An error from a failed call should not persist into a subsequent successful call."""
        from CopySVGTranslation.injection.svg_injector import SVGTranslationInjector

        inner = '<switch><text id="t0"><tspan id="t0">Hello</tspan></text></switch>'
        svg = _write_svg(tmp_path, inner)
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        inj = SVGTranslationInjector()

        # First call: non-existent file → error
        r1 = inj.inject(inject_file=tmp_path / "nonexistent.svg", all_mappings=mappings)
        assert r1.new_stats.error != ""

        # Second call: valid file → should succeed with no error
        r2 = inj.inject(inject_file=svg, all_mappings=mappings)
        assert r2.new_stats.error == "", f"Error persisted from previous call: {r2.new_stats.error!r}"

    def test_error_does_not_persist_after_failed_call(self, tmp_path: Path):
        """Each failed call should have its own error, not the previous one's."""
        from CopySVGTranslation.injection.svg_injector import SVGTranslationInjector

        inj = SVGTranslationInjector()

        # First call: non-existent file
        r1 = inj.inject(inject_file=tmp_path / "nonexistent.svg", all_mappings={"new": {}})
        first_error = r1.new_stats.error
        assert first_error != ""

        # Second call: no mappings
        inner = '<switch><text id="t0"><tspan id="t0">Hello</tspan></text></switch>'
        svg = _write_svg(tmp_path, inner)
        r2 = inj.inject(inject_file=svg, all_mappings=None)
        second_error = r2.new_stats.error

        # Should have its own error, not the first call's
        assert second_error != ""
        assert second_error != first_error, "Second call should have its own error message"

    def test_three_consecutive_calls_produce_correct_stats(self, tmp_path: Path):
        """Three consecutive calls should each produce correct, independent stats."""
        from CopySVGTranslation.injection.svg_injector import SVGTranslationInjector

        inner = '<switch><text id="t0"><tspan id="t0">Hello</tspan></text></switch>'
        svg = _write_svg(tmp_path, inner)
        mappings = {"new": {"hello": {"ar": "مرحبا", "fr": "Bonjour"}}}

        inj = SVGTranslationInjector()

        results = []
        for _ in range(3):
            r = inj.inject(inject_file=svg, all_mappings=mappings)
            results.append(r)

        for i, r in enumerate(results):
            assert r.new_stats.inserted_translations == 2, f"Call {i + 1}: expected 2 insertions"
            assert r.new_stats.processed_switches == 1, f"Call {i + 1}: expected 1 processed switch"


# ===========================================================================
# BUG-02: Extractor accumulates state across calls
# ===========================================================================


class TestExtractorStateIsolation:
    """Verify that SVGTranslationExtractor does not leak state between calls."""

    def test_keys_do_not_accumulate_across_files(self, tmp_path: Path):
        """Extracting from file B should not contain keys from file A."""
        from CopySVGTranslation.extraction.svg_extractor import SVGTranslationExtractor

        svg_a = _write_svg(
            tmp_path,
            """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">مرحبا</tspan></text>
            </switch>
            """,
            name="a.svg",
        )
        svg_b = _write_svg(
            tmp_path,
            """
            <switch>
                <text id="t1"><tspan id="t1">World</tspan></text>
                <text id="t1-fr" systemLanguage="fr"><tspan id="t1-fr">Monde</tspan></text>
            </switch>
            """,
            name="b.svg",
        )

        ext = SVGTranslationExtractor(svg_a)
        r1 = ext.extract()
        assert "hello" in r1.new
        assert "world" not in r1.new

        # Reuse same instance for file B
        ext.svg_file_path = svg_b
        r2 = ext.extract()
        assert "world" in r2.new
        assert "hello" not in r2.new, "Keys from file A leaked into file B extraction"

    def test_returned_objects_are_independent(self, tmp_path: Path):
        """Each extract() call should return a fresh ExtractorData object."""
        from CopySVGTranslation.extraction.svg_extractor import SVGTranslationExtractor

        svg = _write_svg(
            tmp_path,
            """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">مرحبا</tspan></text>
            </switch>
            """,
        )

        ext = SVGTranslationExtractor(svg)
        r1 = ext.extract()
        r2 = ext.extract()

        assert r1 is not r2, "extract() should return different ExtractorData objects"

    def test_tspans_by_id_do_not_accumulate(self, tmp_path: Path):
        """tspans_by_id should only contain IDs from the current file."""
        from CopySVGTranslation.extraction.svg_extractor import SVGTranslationExtractor

        svg_a = _write_svg(
            tmp_path,
            """
            <switch>
                <text id="t-unique-a"><tspan id="t-unique-a">Alpha</tspan></text>
            </switch>
            """,
            name="a.svg",
        )
        svg_b = _write_svg(
            tmp_path,
            """
            <switch>
                <text id="t-unique-b"><tspan id="t-unique-b">Beta</tspan></text>
            </switch>
            """,
            name="b.svg",
        )

        ext = SVGTranslationExtractor(svg_a)
        r1 = ext.extract()
        assert "t-unique-a" in r1.tspans_by_id

        ext.svg_file_path = svg_b
        r2 = ext.extract()
        assert "t-unique-b" in r2.tspans_by_id
        assert "t-unique-a" not in r2.tspans_by_id, "tspans_by_id from file A leaked into file B"

    def test_error_cleared_on_successful_reuse(self, tmp_path: Path):
        """After a parse error, reusing the extractor on a valid file should clear the error."""
        from CopySVGTranslation.extraction.svg_extractor import SVGTranslationExtractor

        # Create a malformed SVG
        bad_svg = tmp_path / "bad.svg"
        bad_svg.write_text("<svg><broken", encoding="utf-8")

        ext = SVGTranslationExtractor(bad_svg)
        r1 = ext.extract()
        assert r1.error != ""

        # Now point to a valid file
        good_svg = _write_svg(
            tmp_path,
            """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
            """,
            name="good.svg",
        )
        ext.svg_file_path = good_svg
        r2 = ext.extract()
        assert r2.error == "", f"Error persisted: {r2.error!r}"


# ===========================================================================
# BUG-04: svg_extract_and_inject not in __all__
# ===========================================================================


class TestPublicAPIExports:
    """Verify that documented public API functions are properly exported."""

    def test_svg_extract_and_inject_importable(self):
        """svg_extract_and_inject should be importable from the top-level package."""
        import CopySVGTranslation

        assert hasattr(CopySVGTranslation, "svg_extract_and_inject")
        assert callable(CopySVGTranslation.svg_extract_and_inject)

    def test_svg_extract_and_injects_importable(self):
        """svg_extract_and_injects should be importable from the top-level package."""
        import CopySVGTranslation

        assert hasattr(CopySVGTranslation, "svg_extract_and_injects")
        assert callable(CopySVGTranslation.svg_extract_and_injects)

    def test_both_in_all(self):
        """Both workflow functions should be listed in __all__."""
        import CopySVGTranslation

        assert "svg_extract_and_inject" in CopySVGTranslation.__all__
        assert "svg_extract_and_injects" in CopySVGTranslation.__all__

    def test_star_import_includes_workflows(self):
        """A star import should include the workflow functions."""
        import CopySVGTranslation

        # Simulate what `from CopySVGTranslation import *` would give
        all_names = CopySVGTranslation.__all__
        assert "svg_extract_and_inject" in all_names
        assert "svg_extract_and_injects" in all_names

    def test_documented_classes_still_exported(self):
        """Ensure existing exports were not removed when adding workflow functions."""
        import CopySVGTranslation

        expected = {
            "SVGTranslationInjector",
            "SVGTranslationExtractor",
            "ExtractorData",
            "InjectorData",
            "svg_extract_and_inject",
            "svg_extract_and_injects",
            "match_nested_tags",
            "fix_nested_file",
        }
        assert expected.issubset(set(CopySVGTranslation.__all__))


# ===========================================================================
# BUG-05: SvgTranslationPreparer not idempotent
# ===========================================================================


class TestPreparerIdempotency:
    """Verify that SvgTranslationPreparer.prepare() is idempotent."""

    def test_prepare_called_twice_produces_same_result(self, tmp_path: Path):
        """Calling prepare() twice should produce structurally equivalent results."""
        from CopySVGTranslation.injection.preparation import SvgTranslationPreparer

        svg = _write_svg(
            tmp_path,
            '<text id="t1"><tspan id="t1">Hello</tspan></text>',
        )

        preparer = SvgTranslationPreparer(svg)

        _tree1, root1 = preparer.prepare()
        xml1 = etree.tostring(root1, encoding="unicode")

        _tree2, root2 = preparer.prepare()
        xml2 = etree.tostring(root2, encoding="unicode")

        assert xml1 == xml2, "Second prepare() call produced different output"

    def test_translatable_nodes_do_not_accumulate(self, tmp_path: Path):
        """translatable_nodes should have the same count after each prepare() call."""
        from CopySVGTranslation.injection.preparation import SvgTranslationPreparer

        svg = _write_svg(
            tmp_path,
            """
            <switch>
                <text id="t1"><tspan id="t1">Hello</tspan></text>
                <text id="t1-fr" systemLanguage="fr"><tspan id="t1-fr">Bonjour</tspan></text>
            </switch>
            """,
        )

        preparer = SvgTranslationPreparer(svg)

        preparer.prepare()
        count_after_first = len(preparer.translatable_nodes)

        preparer.prepare()
        count_after_second = len(preparer.translatable_nodes)

        assert count_after_first == count_after_second, (
            f"translatable_nodes grew from {count_after_first} to {count_after_second}"
        )

    def test_existing_ids_do_not_accumulate(self, tmp_path: Path):
        """existing_ids should have the same count after each prepare() call."""
        from CopySVGTranslation.injection.preparation import SvgTranslationPreparer

        svg = _write_svg(
            tmp_path,
            '<text id="t1"><tspan id="t1">Hello</tspan></text>',
        )

        preparer = SvgTranslationPreparer(svg)

        preparer.prepare()
        ids_after_first = set(preparer.existing_ids)

        preparer.prepare()
        ids_after_second = set(preparer.existing_ids)

        assert ids_after_first == ids_after_second, (
            f"existing_ids changed: {ids_after_first} → {ids_after_second}"
        )

    def test_ids_in_use_reset(self, tmp_path: Path):
        """ids_in_use should be reset between prepare() calls."""
        from CopySVGTranslation.injection.preparation import SvgTranslationPreparer

        # SVG with no IDs → preparer will allocate trsvg IDs
        svg = _write_svg(
            tmp_path,
            "<text>No ID</text>",
        )

        preparer = SvgTranslationPreparer(svg)

        preparer.prepare()
        ids_after_first = list(preparer.ids_in_use)

        preparer.prepare()
        ids_after_second = list(preparer.ids_in_use)

        assert ids_after_first == ids_after_second, (
            f"ids_in_use changed: {ids_after_first} → {ids_after_second}"
        )


# ===========================================================================
# BUG-06: fix_nested_file overwrites input by default
# ===========================================================================


class TestFixNestedFileDeprecation:
    """Verify that fix_nested_file emits a deprecation warning when new_path is None."""

    def test_deprecation_warning_when_new_path_is_none(self, tmp_path: Path):
        """Calling fix_nested_file without new_path should emit DeprecationWarning."""
        from CopySVGTranslation.nested_analyze.find_nested import fix_nested_file

        svg = _write_svg(
            tmp_path,
            '<text id="t1"><tspan id="t1">Hello</tspan></text>',
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            fix_nested_file(svg)

            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1, "Expected DeprecationWarning when new_path is None"
            assert "new_path" in str(deprecation_warnings[0].message).lower() or "deprecated" in str(
                deprecation_warnings[0].message
            ).lower()

    def test_no_warning_when_new_path_provided(self, tmp_path: Path):
        """Calling fix_nested_file with new_path should not emit a warning."""
        from CopySVGTranslation.nested_analyze.find_nested import fix_nested_file

        svg = _write_svg(
            tmp_path,
            '<text id="t1"><tspan id="t1">Hello</tspan></text>',
        )
        output = tmp_path / "output.svg"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            fix_nested_file(svg, new_path=output)

            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) == 0, "Should not warn when new_path is provided"

    def test_new_find_nested_also_warns(self, tmp_path: Path):
        """The find_nested_new module should also emit a deprecation warning."""
        from CopySVGTranslation.nested_analyze.find_nested_new import fix_nested_file as fix_nested_file_new

        svg = _write_svg(
            tmp_path,
            '<text id="t1"><tspan id="t1">Hello</tspan></text>',
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            fix_nested_file_new(svg)

            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1, "find_nested_new should also warn"
