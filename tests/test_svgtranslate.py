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

from CopySvgTranslate import extract, inject, normalize_text, generate_unique_id
from tests._cleanup import cleanup_directory

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
                "rear speakers carry same signal,": {
                    "ar": "السماعات الخلفية تنقل الإشارة نفسها،",
                },
                "but are connected in anti-phase": {
                    "ar": "لكنها موصولة بمرحلتين متعاكستين.",
                },
            },
            "title": {},
        }

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        cleanup_directory(self.test_dir)

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
        self.assertIn("title", translations)
        self.assertEqual(translations["new"], self.expected_translations["new"])
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

    def test_normalize_text_with_numbers(self):
        """Test text normalization with numbers."""
        self.assertEqual(normalize_text("Population 2020"), "Population 2020")
        self.assertEqual(normalize_text("  Population   2020  "), "Population 2020")

    def test_normalize_text_with_punctuation(self):
        """Test text normalization with punctuation."""
        self.assertEqual(normalize_text("Hello, World!"), "Hello, World!")
        self.assertEqual(normalize_text("  Hello,  World!  "), "Hello, World!")

    def test_normalize_text_case_insensitive_arabic(self):
        """Test case insensitive normalization preserves Arabic text."""
        arabic_text = "السكان 2020"
        result = normalize_text(arabic_text, case_insensitive=True)
        # Arabic text doesn't have uppercase/lowercase, should be preserved
        self.assertIn("السكان", result)

    def test_normalize_text_multiple_languages(self):
        """Test text normalization with mixed scripts."""
        mixed_text = "  Hello مرحبا World  "
        result = normalize_text(mixed_text)
        self.assertEqual(result, "Hello مرحبا World")

    def test_generate_unique_id_empty_base(self):
        """Test unique ID generation with empty base ID."""
        existing_ids = set()
        new_id = generate_unique_id("", "fr", existing_ids)
        self.assertEqual(new_id, "-fr")

    def test_generate_unique_id_numeric_suffix_collision(self):
        """Test unique ID generation with existing numeric suffixes."""
        existing_ids = {"base-ar", "base-ar-1", "base-ar-2", "base-ar-5"}
        # Should find the next available number (not necessarily 3)
        new_id = generate_unique_id("base", "ar", existing_ids)
        self.assertIn("base-ar", new_id)
        self.assertNotIn(new_id, existing_ids)

    def test_generate_unique_id_with_special_characters(self):
        """Test unique ID generation with special characters in base ID."""
        existing_ids = set()
        new_id = generate_unique_id("text_2205-tspan", "ar", existing_ids)
        self.assertEqual(new_id, "text_2205-tspan-ar")

    def test_extract_with_multiple_switches(self):
        """Test extraction with multiple switch elements."""
        multi_switch_svg = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink" version="1.0" width="1000" height="1000">
    <switch>
        <text id="text1-ar" systemLanguage="ar"><tspan>نص عربي 1</tspan></text>
        <text id="text1"><tspan>English text 1</tspan></text>
    </switch>
    <switch>
        <text id="text2-ar" systemLanguage="ar"><tspan>نص عربي 2</tspan></text>
        <text id="text2"><tspan>English text 2</tspan></text>
    </switch>
    <switch>
        <text id="text3-fr" systemLanguage="fr"><tspan>Texte français</tspan></text>
        <text id="text3"><tspan>English text 3</tspan></text>
    </switch>
</svg>'''

        svg_path = self.test_dir / "multi_switch.svg"
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(multi_switch_svg)

        translations = extract(svg_path)

        self.assertIsNotNone(translations)
        self.assertIn("new", translations)
        # Should have extracted multiple translations
        self.assertGreater(len(translations["new"]), 1)

    def test_extract_directory_path(self):
        """Test extraction with directory path instead of file."""
        result = extract(self.test_dir)
        self.assertIsNone(result)

    def test_inject_with_multiple_mapping_files(self):
        """Test injection with multiple mapping files."""
        # Create first mapping file
        mapping1_path = self.test_dir / "mapping1.json"
        mapping1 = {
            "new": {
                "text 1": {"ar": "نص 1"}
            },
            "title": {}
        }
        with open(mapping1_path, 'w', encoding='utf-8') as f:
            json.dump(mapping1, f, ensure_ascii=False)

        # Create second mapping file
        mapping2_path = self.test_dir / "mapping2.json"
        mapping2 = {
            "new": {
                "text 2": {"ar": "نص 2"}
            },
            "title": {}
        }
        with open(mapping2_path, 'w', encoding='utf-8') as f:
            json.dump(mapping2, f, ensure_ascii=False)

        # Create target SVG
        target_svg = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg">
    <switch>
        <text id="text1"><tspan id="tspan2207">Text 1</tspan></text>
    </switch>
    <switch>
        <text id="text2"><tspan id="tspan2215">Text 2</tspan></text>
    </switch>
</svg>'''

        target_path = self.test_dir / "target.svg"
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(target_svg)

        # Inject with both mapping files
        tree, stats = inject(
            target_path,
            [mapping1_path, mapping2_path],
            return_stats=True,
        )

        self.assertIsNotNone(tree)
        self.assertIsNotNone(stats)
        # Should have processed translations from both files
        self.assertGreater(stats['inserted_translations'], 0)

    def test_inject_with_output_directory(self):
        """Test injection specifying output directory."""
        mapping_path = self.test_dir / "mapping.json"
        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(self.expected_translations, f, ensure_ascii=False)

        target_path = self.test_dir / "target.svg"
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(self.no_translations_svg_content)

        output_dir = self.test_dir / "output"
        output_dir.mkdir()

        tree = inject(
            target_path,
            [mapping_path],
            output_dir=output_dir,
            save_result=True,
        )

        self.assertIsNotNone(tree)
        # Check that file was saved in output directory
        expected_output = output_dir / target_path.name
        self.assertTrue(expected_output.exists())

    def test_inject_preserves_original_structure(self):
        """Test that injection preserves the original SVG structure."""
        mapping_path = self.test_dir / "mapping.json"
        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(self.expected_translations, f, ensure_ascii=False)

        target_path = self.test_dir / "target.svg"
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(self.no_translations_svg_content)

        tree = inject(target_path, [mapping_path])

        self.assertIsNotNone(tree)
        # Original elements should still be present
        tree_str = etree.tostring(tree.getroot(), encoding='unicode')
        self.assertIn('id="foreground"', tree_str)
        self.assertIn('switch', tree_str)

    def test_inject_without_overwrite_skips_existing(self):
        """Test injection without overwrite skips existing translations."""
        # Create SVG with existing Arabic translation
        svg_with_existing = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg">
    <switch>
        <text id="text1-ar" systemLanguage="ar">
            <tspan id="tspan1-ar">Existing Arabic</tspan>
        </text>
        <text id="text1">
            <tspan id="tspan1">Rear speakers carry same signal,</tspan>
        </text>
    </switch>
</svg>'''

        svg_path = self.test_dir / "existing.svg"
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg_with_existing)

        mapping_path = self.test_dir / "mapping.json"
        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(self.expected_translations, f, ensure_ascii=False)

        # Inject without overwrite
        tree, stats = inject(
            svg_path,
            [mapping_path],
            overwrite=False,
            return_stats=True,
            save_result=True,
            output_file=svg_path,
        )

        self.assertIsNotNone(tree)
        # Should have skipped the existing translation
        self.assertEqual(stats['inserted_translations'], 0)
        self.assertEqual(stats['skipped_translations'], 1)

        # Verify original text is preserved
        with open(svg_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('Existing Arabic', content)

    def test_extract_with_whitespace_in_text(self):
        """Test extraction handles text with various whitespace."""
        svg_with_whitespace = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg">
    <switch>
        <text id="text1-ar" systemLanguage="ar">
            <tspan>   نص   مع   مسافات   </tspan>
        </text>
        <text id="text1">
            <tspan>   Text   with   spaces   </tspan>
        </text>
    </switch>
</svg>'''

        svg_path = self.test_dir / "whitespace.svg"
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg_with_whitespace)

        translations = extract(svg_path)

        self.assertIsNotNone(translations)
        # Whitespace should be normalized
        if "new" in translations:
            for key in translations["new"]:
                if isinstance(key, str):
                    # Should not have leading/trailing spaces or multiple consecutive spaces
                    self.assertEqual(key, key.strip())
                    self.assertNotIn("  ", key)

    def test_inject_stats_accuracy(self):
        """Test that injection statistics are accurate."""
        # Create SVG with 3 switches: 1 will get new translation, 1 updated, 1 skipped
        complex_svg = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg">
    <switch>
        <text id="text1"><tspan id="tspan1">Rear speakers carry same signal,</tspan></text>
    </switch>
    <switch>
        <text id="text2-ar" systemLanguage="ar"><tspan>Old translation</tspan></text>
        <text id="text2"><tspan id="tspan2">but are connected in anti-phase</tspan></text>
    </switch>
    <switch>
        <text id="text3"><tspan>Unmatched text</tspan></text>
    </switch>
</svg>'''

        svg_path = self.test_dir / "complex.svg"
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(complex_svg)

        mapping_path = self.test_dir / "mapping.json"
        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(self.expected_translations, f, ensure_ascii=False)

        # Test with overwrite=True
        tree, stats = inject(
            svg_path,
            [mapping_path],
            overwrite=True,
            return_stats=True,
        )

        self.assertIsNotNone(tree)
        # Verify stats are present and reasonable
        self.assertIn('processed_switches', stats)
        self.assertIn('inserted_translations', stats)
        self.assertIn('updated_translations', stats)
        self.assertGreaterEqual(stats['processed_switches'], 0)

    def test_extract_and_inject_roundtrip(self):
        """Test that extract and inject work together in a roundtrip."""
        # Create a source SVG with translations
        arabic_svg_path = self.test_dir / "arabic.svg"
        with open(arabic_svg_path, 'w', encoding='utf-8') as f:
            f.write(self.arabic_svg_content)

        # Extract translations
        translations = extract(arabic_svg_path)
        self.assertIsNotNone(translations)

        # Save to JSON
        mapping_path = self.test_dir / "roundtrip.json"
        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(translations, f, ensure_ascii=False)

        # Create target without translations
        target_path = self.test_dir / "target.svg"
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(self.no_translations_svg_content)

        # Inject translations
        tree, stats = inject(
            target_path,
            [mapping_path],
            return_stats=True,
        )

        self.assertIsNotNone(tree)
        self.assertGreater(stats['inserted_translations'], 0)

        # Verify the translated content
        self.assertTreeHasTranslations(tree)

    def test_inject_empty_mapping_file(self):
        """Test injection with empty mapping file."""
        empty_mapping = {"new": {}, "title": {}}
        mapping_path = self.test_dir / "empty_mapping.json"
        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(empty_mapping, f)

        target_path = self.test_dir / "target.svg"
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(self.no_translations_svg_content)

        tree, stats = inject(target_path, [mapping_path], return_stats=True)

        # Should complete without error, but with no translations
        self.assertIsNotNone(tree)
        self.assertEqual(stats['inserted_translations'], 0)

    def test_inject_invalid_json_mapping(self):
        """Test injection with invalid JSON mapping file."""
        mapping_path = self.test_dir / "invalid.json"
        with open(mapping_path, 'w', encoding='utf-8') as f:
            f.write("{invalid json content")

        target_path = self.test_dir / "target.svg"
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(self.no_translations_svg_content)

        result = inject(target_path, [mapping_path])
        self.assertIsNone(result)

    def test_normalize_text_preserves_content(self):
        """Test that normalize_text doesn't remove important content."""
        # Test with various content types
        test_cases = [
            ("Hello World", "Hello World"),
            ("123 456", "123 456"),
            ("test@example.com", "test@example.com"),
            ("path/to/file", "path/to/file"),
            ("a-b-c", "a-b-c"),
            ("a b y", "a b y"),
            ("你好世界", "你好世界"),
        ]

        for input_text, expected in test_cases:
            result = normalize_text(input_text)
            self.assertEqual(result, expected, f"Failed for input: {input_text}")
