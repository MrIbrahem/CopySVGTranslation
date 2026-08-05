"""
Unit tests for the SVG translation tool.
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest
from lxml import etree

from CopySVGTranslation.extraction.worker import extract
from CopySVGTranslation.legacy.inject import inject_file_and_save, inject_file_tree


class TestSetup:
    """Test cases for the SVG translation tool."""

    @pytest.fixture(autouse=True)
    def setUp(self, mock_arabic_svg_content, mock_no_translations_svg_content):
        """
        Prepare temporary directory and SVG test fixtures used by the test cases.

        Sets up the following instance attributes for use by tests:
            test_dir: Path to a temporary directory for fixture files.
            arabic_svg_content: SVG string containing English and Arabic switches (two entries).
            no_translations_svg_content: SVG string containing only English switches (two entries).
            expected_arabic_texts: List of the Arabic tspan texts expected to be found in the Arabic SVG.
            expected_translations: Mapping structure representing expected translation mappings for the two English source strings to Arabic.
        """
        self.test_dir = Path(tempfile.mkdtemp())
        self.arabic_svg_content = mock_arabic_svg_content

        self.no_translations_svg_content = mock_no_translations_svg_content

        self.expected_arabic_texts = [
            "السماعات الخلفية تنقل الإشارة نفسها،",
            "لكنها موصولة بمرحلتين متعاكستين.",
        ]

        self.expected_translations = {
            "new": {
                "rear speakers carry same signal,": {
                    "ar": "السماعات الخلفية تنقل الإشارة نفسها،",
                },
                "but are connected in anti-phase": {
                    "ar": "لكنها موصولة بمرحلتين متعاكستين.",
                },
            },
            "title_new": {},
        }

        yield
        """Clean up test fixtures."""
        # Clean up temporary files
        shutil.rmtree(self.test_dir)

    def assert_tree_has_translations(self, tree, expected_texts=None):
        """Verify that the injected tree contains the expected Arabic texts."""
        assert isinstance(tree, etree._ElementTree)
        ns = {"svg": "http://www.w3.org/2000/svg"}
        found_texts = tree.xpath("//svg:text[@systemLanguage='ar']/svg:tspan/text()", namespaces=ns)
        texts_to_check = expected_texts or self.expected_arabic_texts
        for expected in texts_to_check:
            assert expected in found_texts


class TestSVGTranslate(TestSetup):

    def test_extract(self):
        """Test extraction of translations from SVG."""
        # Create test SVG file
        arabic_svg_path = self.test_dir / "arabic.svg"
        with open(arabic_svg_path, "w", encoding="utf-8") as f:
            f.write(self.arabic_svg_content)

        # Extract translations
        translations = extract(arabic_svg_path)

        # Verify translations
        assert translations is not None
        assert "new" in translations
        assert "title_new" in translations
        assert translations["new"] == self.expected_translations["new"]
        assert translations["title_new"] == self.expected_translations["title_new"]

    def test_extract_case_insensitive(self):
        """Test extraction with case insensitive matching."""
        # Create test SVG file
        arabic_svg_path = self.test_dir / "arabic.svg"
        with open(arabic_svg_path, "w", encoding="utf-8") as f:
            f.write(self.arabic_svg_content)

        # Extract translations with case insensitive option
        translations = extract(arabic_svg_path, case_insensitive=True)

        # Verify translations (keys should be lowercase)
        assert translations is not None
        assert "new" in translations
        assert translations["new"] == self.expected_translations["new"]
        assert translations["title_new"] == self.expected_translations["title_new"]

    def test_extract_nonexistent_file(self):
        """Test extraction with non-existent file."""
        nonexistent_path = self.test_dir / "nonexistent.svg"
        translations = extract(nonexistent_path)
        assert translations is None

    def test_inject(self):
        """Test injection of translations into SVG."""
        # Create test files
        arabic_svg_path = self.test_dir / "arabic.svg"
        no_translations_path = self.test_dir / "no_translations.svg"
        mapping_path = self.test_dir / "arabic.svg.json"

        with open(arabic_svg_path, "w", encoding="utf-8") as f:
            f.write(self.arabic_svg_content)

        with open(no_translations_path, "w", encoding="utf-8") as f:
            f.write(self.no_translations_svg_content)

        with open(mapping_path, "w", encoding="utf-8") as f:
            json.dump(self.expected_translations, f, ensure_ascii=False)

        # Inject translations
        tree, stats = inject_file_and_save(
            inject_file=no_translations_path,
            mapping_files=[mapping_path],
            return_stats=True,
            save_path=no_translations_path,
        )

        # Verify stats
        assert tree is not None
        assert stats is not None
        assert stats["processed_switches"] == 2
        assert stats["inserted_translations"] == 2
        assert stats["updated_translations"] == 0
        assert stats["skipped_translations"] == 0

        # Verify the in-memory tree has the translations
        self.assert_tree_has_translations(tree)

        # Verify modified SVG contains translations
        with open(no_translations_path, "r", encoding="utf-8") as f:
            modified_svg = f.read()

        assert 'systemLanguage="ar"' in modified_svg
        assert "السماعات الخلفية تنقل الإشارة نفسها،" in modified_svg
        assert "لكنها موصولة بمرحلتين متعاكستين." in modified_svg

    def test_inject_dry_run(self):
        """Test injection in dry-run mode."""
        # Create test files
        arabic_svg_path = self.test_dir / "arabic.svg"
        no_translations_path = self.test_dir / "no_translations.svg"
        mapping_path = self.test_dir / "arabic.svg.json"

        with open(arabic_svg_path, "w", encoding="utf-8") as f:
            f.write(self.arabic_svg_content)

        with open(no_translations_path, "w", encoding="utf-8") as f:
            f.write(self.no_translations_svg_content)

        with open(mapping_path, "w", encoding="utf-8") as f:
            json.dump(self.expected_translations, f, ensure_ascii=False)

        # Get original file content
        with open(no_translations_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        # Inject translations in dry-run mode
        tree, stats = inject_file_tree(
            inject_file=no_translations_path,
            mapping_files=[mapping_path],
            return_stats=True,
        )

        # Verify stats
        assert tree is not None
        assert stats is not None
        assert stats["processed_switches"] == 2
        assert stats["inserted_translations"] == 2

        # Verify file was not modified
        with open(no_translations_path, "r", encoding="utf-8") as f:
            current_content = f.read()

        assert original_content == current_content

        # Verify the in-memory tree has the translations
        self.assert_tree_has_translations(tree)

    def test_inject_overwrite(self):
        """Test injection with overwrite option."""
        # Create test SVG with existing translations
        svg_with_existing = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink" version="1.0" width="1000" height="1000" id="svg2235">
    <g id="foreground">
        <switch style="font-size:30px;font-family:Bitstream Vera Sans">
            <text x="250.88867" y="847.29651" style="font-size:30px;font-family:Bitstream Vera Sans"
                id="text2205-ar"
                xml:space="preserve" systemLanguage="ar">
                <tspan x="250.88867" y="847.29651" id="tspan2207-ar">Old translation</tspan>
            </text>
            <text x="250.88867" y="847.29651" style="font-size:30px;font-family:Bitstream Vera Sans"
                id="text2205"
                xml:space="preserve">
                <tspan x="250.88867" y="847.29651" id="tspan2207">Rear speakers carry same signal,</tspan>
            </text>
        </switch>
    </g>
</svg>"""

        # Create test files
        svg_path = self.test_dir / "test.svg"
        mapping_path = self.test_dir / "arabic.svg.json"

        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_with_existing)

        with open(mapping_path, "w", encoding="utf-8") as f:
            json.dump(self.expected_translations, f, ensure_ascii=False)

        # Inject translations with overwrite
        tree, stats = inject_file_and_save(
            inject_file=svg_path,
            mapping_files=[mapping_path],
            overwrite=True,
            return_stats=True,
            save_path=svg_path,
        )

        # Verify stats
        assert tree is not None
        assert stats is not None
        assert stats["processed_switches"] == 1
        assert stats["inserted_translations"] == 0
        assert stats["updated_translations"] == 1
        assert stats["skipped_translations"] == 0

        # Verify the in-memory tree has the translations
        self.assert_tree_has_translations(tree, [self.expected_arabic_texts[0]])

        # Verify translation was updated
        with open(svg_path, "r", encoding="utf-8") as f:
            modified_svg = f.read()

        assert "السماعات الخلفية تنقل الإشارة نفسها،" in modified_svg
        assert "Old translation" not in modified_svg

    def test_inject_nonexistent_file(self):
        """Test injection with non-existent file."""
        nonexistent_path = self.test_dir / "nonexistent.svg"
        mapping_path = self.test_dir / "arabic.svg.json"

        with open(mapping_path, "w", encoding="utf-8") as f:
            json.dump(self.expected_translations, f, ensure_ascii=False)

        result = inject_file_tree(inject_file=nonexistent_path, mapping_files=[mapping_path])
        assert result is None

    def test_inject_nonexistent_mapping(self):
        """Test injection with non-existent mapping file."""
        svg_path = self.test_dir / "test.svg"
        nonexistent_mapping = self.test_dir / "nonexistent.json"

        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(self.no_translations_svg_content)

        result = inject_file_tree(
            inject_file=svg_path,
            mapping_files=[nonexistent_mapping],
        )
        assert result is None
