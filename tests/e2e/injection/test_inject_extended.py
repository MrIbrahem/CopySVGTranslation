"""
Extended comprehensive unit tests for CopySVGTranslation covering additional edge cases
and previously untested functions.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from CopySVGTranslation import SVGTranslationService, TranslationConfig


class TestSetup:
    @pytest.fixture(autouse=True)
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self._output_dir = self.test_dir / "output"
        self._output_dir.mkdir()

        yield
        """Clean up test fixtures."""
        # Clean up temporary files
        shutil.rmtree(self.test_dir)


class TestInjectEdgeCases(TestSetup):
    """Test suite for inject edge cases."""

    def test_inject_with_invalid_svg_structure(self):
        """Test inject with invalid SVG structure."""
        svg_path = self.test_dir / "invalid.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <text id="bad|id">Test</text>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        mappings = {"new": {"test": {"ar": "اختبار"}}}

        service = SVGTranslationService()
        result = service.inject(svg_path=svg_path, mapping=mappings, output=svg_path)

        assert not result.success
        assert result.error is not None

    def test_inject_case_insensitive_false(self):
        """Test inject with case-sensitive matching."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t1"><tspan>Hello</tspan></text></switch>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        mappings = {"new": {"Hello": {"ar": "مرحبا"}}}

        service = SVGTranslationService(TranslationConfig(case_insensitive=False))
        result = service.inject(svg_path=svg_path, mapping=mappings, output=svg_path)

        assert result.success
        assert result.data is not None
        assert result.data.tree is not None

    def test_inject_save_result_creates_output_file(self):
        """Test that save=True with output creates the output file."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t1"><tspan>Hello</tspan></text></switch>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        _output_file = self.test_dir / "output.svg"
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        service = SVGTranslationService()
        result = service.inject(
            svg_path=svg_path,
            mapping=mappings,
            output=_output_file,
            save=True,
        )

        assert result.success
        assert _output_file.exists() is True
