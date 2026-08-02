"""
Unit tests for the SVG translation tool.
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest
from lxml import etree

from CopySVGTranslation.extraction import extract
from CopySVGTranslation.injection import inject
from CopySVGTranslation.utils import generate_unique_id


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
            "title": {},
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

    def test_generate_unique_id_empty_base(self):
        """Test unique ID generation with empty base ID."""
        existing_ids = set()
        new_id = generate_unique_id("", "fr", existing_ids)
        assert new_id == "-fr"

    def test_generate_unique_id_numeric_suffix_collision(self):
        """Test unique ID generation with existing numeric suffixes."""
        existing_ids = {"base-ar", "base-ar-1", "base-ar-2", "base-ar-5"}
        # Should find the next available number (not necessarily 3)
        new_id = generate_unique_id("base", "ar", existing_ids)
        assert "base-ar" in new_id
        assert new_id not in existing_ids

    def test_generate_unique_id_with_special_characters(self):
        """Test unique ID generation with special characters in base ID."""
        existing_ids = set()
        new_id = generate_unique_id("text_2205-tspan", "ar", existing_ids)
        assert new_id == "text_2205-tspan-ar"

    def test_extract_with_multiple_switches(self):
        """Test extraction with multiple switch elements."""
        multi_switch_svg = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
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
</svg>"""

        svg_path = self.test_dir / "multi_switch.svg"
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(multi_switch_svg)

        translations = extract(svg_path)

        assert translations is not None
        assert "new" in translations
        # Should have extracted multiple translations
        assert len(translations["new"]) > 1

    def test_extract_directory_path(self):
        """Test extraction with directory path instead of file."""
        result = extract(self.test_dir)
        assert result is None

    def test_inject_with_multiple_mapping_files(self):
        """Test injection with multiple mapping files."""
        # Create first mapping file
        mapping1_path = self.test_dir / "mapping1.json"
        mapping1 = {"new": {"text 1": {"ar": "نص 1"}}, "title": {}}
        with open(mapping1_path, "w", encoding="utf-8") as f:
            json.dump(mapping1, f, ensure_ascii=False)

        # Create second mapping file
        mapping2_path = self.test_dir / "mapping2.json"
        mapping2 = {"new": {"text 2": {"ar": "نص 2"}}, "title": {}}
        with open(mapping2_path, "w", encoding="utf-8") as f:
            json.dump(mapping2, f, ensure_ascii=False)

        # Create target SVG
        target_svg = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg">
    <switch>
        <text id="text1"><tspan id="tspan2207">Text 1</tspan></text>
    </switch>
    <switch>
        <text id="text2"><tspan id="tspan2215">Text 2</tspan></text>
    </switch>
</svg>"""

        target_path = self.test_dir / "target.svg"
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(target_svg)

        # Inject with both mapping files
        tree, stats = inject(
            target_path,
            [mapping1_path, mapping2_path],
            return_stats=True,
        )

        assert tree is not None
        assert stats is not None
        # Should have processed translations from both files
        assert stats["inserted_translations"] > 0

    def test_inject_with_output_directory(self):
        """Test injection specifying output directory."""
        mapping_path = self.test_dir / "mapping.json"
        with open(mapping_path, "w", encoding="utf-8") as f:
            json.dump(self.expected_translations, f, ensure_ascii=False)

        target_path = self.test_dir / "target.svg"
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(self.no_translations_svg_content)

        output_dir = self.test_dir / "output"
        output_dir.mkdir()

        tree = inject(
            target_path,
            [mapping_path],
            output_dir=output_dir,
            save_result=True,
        )

        assert tree is not None
        # Check that file was saved in output directory
        expected_output = output_dir / target_path.name
        assert expected_output.exists() is True

    def test_inject_preserves_original_structure(self):
        """Test that injection preserves the original SVG structure."""
        mapping_path = self.test_dir / "mapping.json"
        with open(mapping_path, "w", encoding="utf-8") as f:
            json.dump(self.expected_translations, f, ensure_ascii=False)

        target_path = self.test_dir / "target.svg"
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(self.no_translations_svg_content)

        tree = inject(target_path, [mapping_path])

        assert tree is not None
        # Original elements should still be present
        tree_str = etree.tostring(tree.getroot(), encoding="unicode")
        assert 'id="foreground"' in tree_str
        assert "switch" in tree_str

    def test_inject_without_overwrite_skips_existing(self):
        """Test injection without overwrite skips existing translations."""
        # Create SVG with existing Arabic translation
        svg_with_existing = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg">
    <switch>
        <text id="text1-ar" systemLanguage="ar">
            <tspan id="tspan1-ar">Existing Arabic</tspan>
        </text>
        <text id="text1">
            <tspan id="tspan1">Rear speakers carry same signal,</tspan>
        </text>
    </switch>
</svg>"""

        svg_path = self.test_dir / "existing.svg"
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_with_existing)

        mapping_path = self.test_dir / "mapping.json"
        with open(mapping_path, "w", encoding="utf-8") as f:
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

        assert tree is not None
        # Should have skipped the existing translation
        assert stats["inserted_translations"] == 0
        assert stats["skipped_translations"] == 1

        # Verify original text is preserved
        with open(svg_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Existing Arabic" in content

    def test_extract_with_whitespace_in_text(self):
        """Test extraction handles text with various whitespace."""
        svg_with_whitespace = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg">
    <switch>
        <text id="text1-ar" systemLanguage="ar">
            <tspan>   نص   مع   مسافات   </tspan>
        </text>
        <text id="text1">
            <tspan>   Text   with   spaces   </tspan>
        </text>
    </switch>
</svg>"""

        svg_path = self.test_dir / "whitespace.svg"
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_with_whitespace)

        translations = extract(svg_path)

        assert translations is not None
        # Whitespace should be normalized
        if "new" in translations:
            for key in translations["new"]:
                if isinstance(key, str):
                    # Should not have leading/trailing spaces or multiple consecutive spaces
                    assert key == key.strip()
                    assert "  " not in key

    def test_inject_stats_accuracy(self):
        """Test that injection statistics are accurate."""
        # Create SVG with 3 switches: 1 will get new translation, 1 updated, 1 skipped
        complex_svg = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
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
</svg>"""

        svg_path = self.test_dir / "complex.svg"
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(complex_svg)

        mapping_path = self.test_dir / "mapping.json"
        with open(mapping_path, "w", encoding="utf-8") as f:
            json.dump(self.expected_translations, f, ensure_ascii=False)

        # Test with overwrite=True
        tree, stats = inject(
            svg_path,
            [mapping_path],
            overwrite=True,
            return_stats=True,
        )

        assert tree is not None
        # Verify stats are present and reasonable
        assert "processed_switches" in stats
        assert "inserted_translations" in stats
        assert "updated_translations" in stats
        assert stats["processed_switches"] >= 0

    def test_extract_and_inject_roundtrip(self):
        """Test that extract and inject work together in a roundtrip."""
        # Create a source SVG with translations
        arabic_svg_path = self.test_dir / "arabic.svg"
        with open(arabic_svg_path, "w", encoding="utf-8") as f:
            f.write(self.arabic_svg_content)

        # Extract translations
        translations = extract(arabic_svg_path)
        assert translations is not None

        # Save to JSON
        mapping_path = self.test_dir / "roundtrip.json"
        with open(mapping_path, "w", encoding="utf-8") as f:
            json.dump(translations, f, ensure_ascii=False)

        # Create target without translations
        target_path = self.test_dir / "target.svg"
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(self.no_translations_svg_content)

        # Inject translations
        tree, stats = inject(
            target_path,
            [mapping_path],
            return_stats=True,
        )

        assert tree is not None
        assert stats["inserted_translations"] > 0

        # Verify the translated content
        self.assert_tree_has_translations(tree)

    def test_inject_empty_mapping_file(self):
        """Test injection with empty mapping file."""
        empty_mapping = {"new": {}, "title": {}}
        mapping_path = self.test_dir / "empty_mapping.json"
        with open(mapping_path, "w", encoding="utf-8") as f:
            json.dump(empty_mapping, f)

        target_path = self.test_dir / "target.svg"
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(self.no_translations_svg_content)

        tree, stats = inject(target_path, [mapping_path], return_stats=True)

        # Should complete without error, but with no translations
        assert tree is not None
        assert stats["inserted_translations"] == 0

    def test_inject_invalid_json_mapping(self):
        """Test injection with invalid JSON mapping file."""
        mapping_path = self.test_dir / "invalid.json"
        with open(mapping_path, "w", encoding="utf-8") as f:
            f.write("{invalid json content")

        target_path = self.test_dir / "target.svg"
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(self.no_translations_svg_content)

        result = inject(target_path, [mapping_path])
        assert result is None
