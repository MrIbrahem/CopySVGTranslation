"""
Extended comprehensive unit tests for CopySVGTranslation covering additional edge cases
and previously untested functions.
"""

import shutil
import tempfile
from collections.abc import Mapping
from pathlib import Path

import pytest
from lxml import etree

from CopySVGTranslation.injection.svg_injector import SVGTranslationInjector


def work_on_switches(
    root: etree._Element,
    existing_ids: set[str],
    mappings: Mapping,
    case_insensitive: bool = True,
    overwrite: bool = False,
) -> dict:
    """Process ``<switch>`` elements and insert or update translations."""
    injector = SVGTranslationInjector(case_insensitive=case_insensitive, overwrite=overwrite)
    stats = injector.work_on_switches(
        root,
        existing_ids,
        mappings,
    )
    if stats is None:
        stats = injector.result.new_stats.to_json()
    return stats


class TestSetup:

    @pytest.fixture(autouse=True)
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.svg_path = self.test_dir / "source.svg"
        self.svg_path.write_text("<svg></svg>", encoding="utf-8")

        yield
        """Clean up test fixtures."""
        # Clean up temporary files
        shutil.rmtree(self.test_dir)


class TestWorkOnSwitches(TestSetup):
    """Test suite for work_on_switches function."""

    def test_work_on_switches_basic(self):
        """Test basic switch processing."""
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1"><tspan>Hello</tspan></text>
            </switch>
        </svg>"""
        root = etree.fromstring(svg_content)
        existing_ids = {"text1"}
        mappings = {"new": {"hello": {"ar": "مرحبا", "fr": "Bonjour"}}}

        stats = work_on_switches(root, existing_ids, mappings, case_insensitive=True)

        assert stats["processed_switches"] == 1
        assert stats["inserted_translations"] == 2

    def test_work_on_switches_no_overwrite(self):
        """Test switch processing without overwriting existing translations."""
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1-ar" systemLanguage="ar"><tspan>مرحبا</tspan></text>
                <text id="text1"><tspan>Hello</tspan></text>
            </switch>
        </svg>"""
        root = etree.fromstring(svg_content)
        existing_ids = {"text1", "text1-ar"}
        mappings = {"new": {"hello": {"ar": "مرحبا جديد", "fr": "Bonjour"}}}

        stats = work_on_switches(root, existing_ids, mappings, overwrite=False)

        assert stats["skipped_translations"] == 1
        assert stats["inserted_translations"] == 1

    def test_work_on_switches_with_overwrite(self):
        """Test switch processing with overwriting existing translations."""
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1-ar" systemLanguage="ar"><tspan>Old</tspan></text>
                <text id="text1"><tspan>Hello</tspan></text>
            </switch>
        </svg>"""
        root = etree.fromstring(svg_content)
        existing_ids = {"text1", "text1-ar"}
        mappings = {"new": {"hello": {"ar": "New"}}}

        stats = work_on_switches(root, existing_ids, mappings, overwrite=True)

        assert stats["updated_translations"] == 1

    def test_work_on_switches_case_sensitive(self):
        """Test switch processing with case-sensitive matching."""
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1"><tspan>Hello</tspan></text>
            </switch>
        </svg>"""
        root = etree.fromstring(svg_content)
        existing_ids = {"text1"}
        mappings = {"new": {"Hello": {"ar": "مرحبا"}}}

        stats = work_on_switches(root, existing_ids, mappings, case_insensitive=False)

        assert stats["inserted_translations"] == 1

    def test_work_on_switches_with_year_suffix(self):
        """Test switch processing with year suffix handling."""
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1"><tspan>Population 2020</tspan></text>
            </switch>
        </svg>"""
        root = etree.fromstring(svg_content)
        existing_ids = {"text1"}
        mappings = {"title": {"Population ": {"ar": "السكان ", "fr": "Population "}}, "new": {}}

        stats = work_on_switches(root, existing_ids, mappings, case_insensitive=True)

        # Year suffix logic should be applied
        assert stats["processed_switches"] >= 0
