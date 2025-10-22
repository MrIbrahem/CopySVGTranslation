#!/usr/bin/env python3
"""
Unit tests for the SVG translation tool.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

from lxml import etree

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from SvgTranslate import extract, inject, normalize_text, generate_unique_id


class TestSVGTranslate(unittest.TestCase):
    """Test cases for the SVG translation tool."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.arabic_svg_content = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink" version="1.0" width="1000" height="1000" id="svg2235">
    <g id="foreground">
        <switch style="font-size:30px;font-family:Bitstream Vera Sans">
            <text x="250.88867" y="847.29651" style="font-size:30px;font-family:Bitstream Vera Sans"
                id="text2205-ar"
                xml:space="preserve" systemLanguage="ar">
                <tspan x="250.88867" y="847.29651" id="tspan2207-ar">السماعات الخلفية تنقل الإشارة نفسها،</tspan>
            </text>
            <text x="250.88867" y="847.29651" style="font-size:30px;font-family:Bitstream Vera Sans"
                id="text2205"
                xml:space="preserve">
                <tspan x="250.88867" y="847.29651" id="tspan2207">Rear speakers carry same signal,</tspan>
            </text>
        </switch>
        <switch style="font-size:30px;font-family:Bitstream Vera Sans">
            <text x="259.34814" y="927.29651" style="font-size:30px;font-family:Bitstream Vera Sans"
                id="text2213-ar"
                xml:space="preserve" systemLanguage="ar">
                <tspan x="259.34814" y="927.29651" id="tspan2215-ar">لكنها موصولة بمرحلتين متعاكستين.</tspan>
            </text>
            <text x="259.34814" y="927.29651" style="font-size:30px;font-family:Bitstream Vera Sans"
                id="text2213"
                xml:space="preserve">
                <tspan x="259.34814" y="927.29651" id="tspan2215">but are connected in anti-phase</tspan>
            </text>
        </switch>
    </g>
</svg>'''

        self.no_translations_svg_content = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink" version="1.0" width="1000" height="1000" id="svg2235">
    <g id="foreground">
        <switch style="font-size:30px;font-family:Bitstream Vera Sans">
            <text x="250.88867" y="847.29651" style="font-size:30px;font-family:Bitstream Vera Sans"
                id="text2205"
                xml:space="preserve">
                <tspan x="250.88867" y="847.29651" id="tspan2207">Rear speakers carry same signal,</tspan>
            </text>
        </switch>
        <switch style="font-size:30px;font-family:Bitstream Vera Sans">
            <text x="259.34814" y="927.29651" style="font-size:30px;font-family:Bitstream Vera Sans"
                id="text2213"
                xml:space="preserve">
                <tspan x="259.34814" y="927.29651" id="tspan2215">but are connected in anti-phase</tspan>
            </text>
        </switch>
    </g>
</svg>'''

        self.expected_arabic_texts = [
            "السماعات الخلفية تنقل الإشارة نفسها،",
            "لكنها موصولة بمرحلتين متعاكستين.",
        ]

        self.expected_translations = {
            "new": {
                "default_tspans_by_id": {
                    "tspan2207": "Rear speakers carry same signal,",
                    "tspan2215": "but are connected in anti-phase",
                },
                "rear speakers carry same signal,": {
                    "ar": "السماعات الخلفية تنقل الإشارة نفسها،",
                },
                "but are connected in anti-phase": {
                    "ar": "لكنها موصولة بمرحلتين متعاكستين.",
                },
            },
            "old_way": {
                "rear speakers carry same signal,": {
                    "_texts": ["rear speakers carry same signal,"],
                    "_translations": {
                        "ar": ["السماعات الخلفية تنقل الإشارة نفسها،"],
                    },
                },
                "but are connected in anti-phase": {
                    "_texts": ["but are connected in anti-phase"],
                    "_translations": {
                        "ar": ["لكنها موصولة بمرحلتين متعاكستين."],
                    },
                },
            },
            "title": {},
        }

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        for file in self.test_dir.glob('*'):
            file.unlink()
        self.test_dir.rmdir()

    def assertTreeHasTranslations(self, tree, expected_texts=None):
        """Verify that the injected tree contains the expected Arabic texts."""
        self.assertIsInstance(tree, etree._ElementTree)
        ns = {"svg": "http://www.w3.org/2000/svg"}
        found_texts = tree.xpath("//svg:text[@systemLanguage='ar']/svg:tspan/text()", namespaces=ns)
        texts_to_check = expected_texts or self.expected_arabic_texts
        for expected in texts_to_check:
            self.assertIn(expected, found_texts)

    def test_normalize_text(self):
        """Test text normalization."""
        self.assertEqual(normalize_text("  hello  world  "), "hello world")
        self.assertEqual(normalize_text("hello    world"), "hello world")
        self.assertEqual(normalize_text("  hello world  "), "hello world")
        self.assertEqual(normalize_text(""), "")
        self.assertEqual(normalize_text(None), "")

    def test_generate_unique_id(self):
        """Test unique ID generation."""
        existing_ids = {"id1", "id2", "id1-ar"}

        # Test with no collision
        new_id = generate_unique_id("id1", "fr", existing_ids)
        self.assertEqual(new_id, "id1-fr")

        # Test with collision
        new_id = generate_unique_id("id1", "ar", existing_ids)
        self.assertEqual(new_id, "id1-ar-1")

        # Test with multiple collisions
        existing_ids.add("id1-ar-1")
        new_id = generate_unique_id("id1", "ar", existing_ids)
        self.assertEqual(new_id, "id1-ar-2")

    def test_extract(self):
        """Test extraction of translations from SVG."""
        # Create test SVG file
        arabic_svg_path = self.test_dir / "arabic.svg"
        with open(arabic_svg_path, 'w', encoding='utf-8') as f:
            f.write(self.arabic_svg_content)

        # Extract translations
        translations = extract(arabic_svg_path)

        # Verify translations
        self.assertIsNotNone(translations)
        self.assertIn("new", translations)
        self.assertIn("old_way", translations)
        self.assertIn("title", translations)
        self.assertEqual(translations["new"], self.expected_translations["new"])
        self.assertEqual(translations["old_way"], self.expected_translations["old_way"])
        self.assertEqual(translations["title"], self.expected_translations["title"])

    def test_extract_case_insensitive(self):
        """Test extraction with case insensitive matching."""
        # Create test SVG file
        arabic_svg_path = self.test_dir / "arabic.svg"
        with open(arabic_svg_path, 'w', encoding='utf-8') as f:
            f.write(self.arabic_svg_content)

        # Extract translations with case insensitive option
        translations = extract(arabic_svg_path, case_insensitive=True)

        # Verify translations (keys should be lowercase)
        self.assertIsNotNone(translations)
        self.assertIn("new", translations)
        self.assertEqual(translations["new"], self.expected_translations["new"])
        self.assertEqual(translations["old_way"], self.expected_translations["old_way"])
        self.assertEqual(translations["title"], self.expected_translations["title"])

    def test_extract_nonexistent_file(self):
        """Test extraction with non-existent file."""
        nonexistent_path = self.test_dir / "nonexistent.svg"
        translations = extract(nonexistent_path)
        self.assertIsNone(translations)

    def test_inject(self):
        """Test injection of translations into SVG."""
        # Create test files
        arabic_svg_path = self.test_dir / "arabic.svg"
        no_translations_path = self.test_dir / "no_translations.svg"
        mapping_path = self.test_dir / "arabic.svg.json"

        with open(arabic_svg_path, 'w', encoding='utf-8') as f:
            f.write(self.arabic_svg_content)

        with open(no_translations_path, 'w', encoding='utf-8') as f:
            f.write(self.no_translations_svg_content)

        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(self.expected_translations, f, ensure_ascii=False)

        # Inject translations
        tree, stats = inject(
            no_translations_path,
            [mapping_path],
            return_stats=True,
            save_result=True,
            output_file=no_translations_path,
        )

        # Verify stats
        self.assertIsNotNone(tree)
        self.assertIsNotNone(stats)
        self.assertEqual(stats['processed_switches'], 2)
        self.assertEqual(stats['inserted_translations'], 2)
        self.assertEqual(stats['updated_translations'], 0)
        self.assertEqual(stats['skipped_translations'], 0)

        # Verify the in-memory tree has the translations
        self.assertTreeHasTranslations(tree)

        # Verify modified SVG contains translations
        with open(no_translations_path, 'r', encoding='utf-8') as f:
            modified_svg = f.read()

        self.assertIn('systemLanguage="ar"', modified_svg)
        self.assertIn('السماعات الخلفية تنقل الإشارة نفسها،', modified_svg)
        self.assertIn('لكنها موصولة بمرحلتين متعاكستين.', modified_svg)

    def test_inject_dry_run(self):
        """Test injection in dry-run mode."""
        # Create test files
        arabic_svg_path = self.test_dir / "arabic.svg"
        no_translations_path = self.test_dir / "no_translations.svg"
        mapping_path = self.test_dir / "arabic.svg.json"

        with open(arabic_svg_path, 'w', encoding='utf-8') as f:
            f.write(self.arabic_svg_content)

        with open(no_translations_path, 'w', encoding='utf-8') as f:
            f.write(self.no_translations_svg_content)

        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(self.expected_translations, f, ensure_ascii=False)

        # Get original file content
        with open(no_translations_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # Inject translations in dry-run mode
        tree, stats = inject(no_translations_path, [mapping_path], return_stats=True)

        # Verify stats
        self.assertIsNotNone(tree)
        self.assertIsNotNone(stats)
        self.assertEqual(stats['processed_switches'], 2)
        self.assertEqual(stats['inserted_translations'], 2)

        # Verify file was not modified
        with open(no_translations_path, 'r', encoding='utf-8') as f:
            current_content = f.read()

        self.assertEqual(original_content, current_content)

        # Verify the in-memory tree has the translations
        self.assertTreeHasTranslations(tree)

    def test_inject_overwrite(self):
        """Test injection with overwrite option."""
        # Create test SVG with existing translations
        svg_with_existing = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
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
</svg>'''

        # Create test files
        svg_path = self.test_dir / "test.svg"
        mapping_path = self.test_dir / "arabic.svg.json"

        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg_with_existing)

        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(self.expected_translations, f, ensure_ascii=False)

        # Inject translations with overwrite
        tree, stats = inject(
            svg_path,
            [mapping_path],
            overwrite=True,
            return_stats=True,
            save_result=True,
            output_file=svg_path,
        )

        # Verify stats
        self.assertIsNotNone(tree)
        self.assertIsNotNone(stats)
        self.assertEqual(stats['processed_switches'], 1)
        self.assertEqual(stats['inserted_translations'], 0)
        self.assertEqual(stats['updated_translations'], 1)
        self.assertEqual(stats['skipped_translations'], 0)

        # Verify the in-memory tree has the translations
        self.assertTreeHasTranslations(tree, [self.expected_arabic_texts[0]])

        # Verify translation was updated
        with open(svg_path, 'r', encoding='utf-8') as f:
            modified_svg = f.read()

        self.assertIn('السماعات الخلفية تنقل الإشارة نفسها،', modified_svg)
        self.assertNotIn('Old translation', modified_svg)

    def test_inject_nonexistent_file(self):
        """Test injection with non-existent file."""
        nonexistent_path = self.test_dir / "nonexistent.svg"
        mapping_path = self.test_dir / "arabic.svg.json"

        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(self.expected_translations, f, ensure_ascii=False)

        result = inject(nonexistent_path, [mapping_path])
        self.assertIsNone(result)

    def test_inject_nonexistent_mapping(self):
        """Test injection with non-existent mapping file."""
        svg_path = self.test_dir / "test.svg"
        nonexistent_mapping = self.test_dir / "nonexistent.json"

        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(self.no_translations_svg_content)

        result = inject(svg_path, [nonexistent_mapping])
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
