"""
Extended comprehensive unit tests for CopySVGTranslation covering additional edge cases
and previously untested functions.
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from CopySVGTranslation.injection import inject


class TestSetup:
    @pytest.fixture(autouse=True)
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.test_dir / "output"
        self.output_dir.mkdir()

        yield
        """Clean up test fixtures."""
        # Clean up temporary files
        shutil.rmtree(self.test_dir)


class TestInjectEdgeCases(TestSetup):
    """Test suite for inject function edge cases."""

    def test_inject_with_invalid_svg_structure(self):
        """Test inject with invalid SVG structure."""
        svg_path = self.test_dir / "invalid.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <text id="bad|id">Test</text>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        mappings = {"new": {"test": {"ar": "اختبار"}}}

        result, stats = inject(svg_path, all_mappings=mappings, return_stats=True)

        assert result is None
        assert "error" in stats

    def test_inject_case_insensitive_false(self):
        """Test inject with case-sensitive matching."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t1"><tspan>Hello</tspan></text></switch>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        mappings = {"new": {"Hello": {"ar": "مرحبا"}}}

        result = inject(svg_path, all_mappings=mappings, case_insensitive=False)

        assert result is not None

    def test_inject_save_result_creates_output_file(self):
        """Test that save_result=True creates the output file."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t1"><tspan>Hello</tspan></text></switch>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        output_file = self.test_dir / "output.svg"
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        inject(svg_path, all_mappings=mappings, output_file=output_file, save_result=True)

        assert output_file.exists() is True

    def test_inject_without_save_result_no_file_created(self):
        """Test that save_result=False doesn't create output file."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t1"><tspan>Hello</tspan></text></switch>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        output_file = self.test_dir / "output.svg"
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        inject(svg_path, all_mappings=mappings, output_file=output_file, save_result=False)

        assert output_file.exists() is False
