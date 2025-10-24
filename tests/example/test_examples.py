"""Comprehensive tests for the CopySvgTranslate public API module (__init__.py)."""

from __future__ import annotations

from pathlib import Path

from CopySvgTranslate import (
    extract,
    svg_extract_and_inject,
    svg_extract_and_injects,
)

FIXTURES_DIR = Path(__file__).parent


class TestIntegrationWorkflows:
    """Integration tests for high-level workflow functions."""

    def test_svg_extract_and_inject_end_to_end(self, tmp_path: Path):
        """Test complete extract and inject workflow."""
        source_svg = FIXTURES_DIR / "source.svg"
        target_svg = tmp_path / "before_translate.svg"
        output_svg = tmp_path / "output.svg"
        data_file = tmp_path / "data.json"

        # Copy target fixture
        target_svg.write_text(
            (FIXTURES_DIR / "before_translate.svg").read_text(encoding="utf-8"),
            encoding="utf-8"
        )

        # Run the workflow
        result = svg_extract_and_inject(
            source_svg,
            target_svg,
            output_file=output_svg,
            data_output_file=data_file,
            save_result=True,
        )

        assert result is not None
        assert output_svg.exists()
        assert data_file.exists()

    def test_svg_extract_and_injects_with_dict(self, tmp_path: Path):
        """Test inject with pre-extracted translations dict."""
        target_svg = tmp_path / "before_translate.svg"
        target_svg.write_text(
            (FIXTURES_DIR / "before_translate.svg").read_text(encoding="utf-8"),
            encoding="utf-8"
        )

        # Extract translations first
        translations = extract(FIXTURES_DIR / "source.svg")

        # Inject using the dict
        result, stats = svg_extract_and_injects(
            translations,
            target_svg,
            output_dir=tmp_path,
            save_result=True,
            return_stats=True,
        )

        assert result is not None
        assert isinstance(stats, dict)
        assert "inserted_translations" in stats
