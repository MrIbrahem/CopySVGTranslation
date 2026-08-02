"""Test configuration for the CopySVGTranslation test-suite."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest
from lxml import etree


@pytest.fixture
def mock_no_translations_svg_content():
    return """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
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
    </svg>"""


@pytest.fixture
def mock_arabic_svg_content():
    return """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
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
    </svg>"""


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
