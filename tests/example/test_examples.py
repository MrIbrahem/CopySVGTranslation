"""Comprehensive tests for the CopySvgTranslate public API module (__init__.py)."""

from __future__ import annotations

from pathlib import Path

from CopySvgTranslate import (
    extract,
    svg_extract_and_inject,
    inject,
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

    def test_inject_with_dict(self, tmp_path: Path):
        """Test inject with pre-extracted translations dict."""
        target_svg = tmp_path / "before_translate.svg"
        target_svg.write_text(
            (FIXTURES_DIR / "before_translate.svg").read_text(encoding="utf-8"),
            encoding="utf-8"
        )

        # Extract translations first
        translations = extract(FIXTURES_DIR / "source.svg")

        # Inject using the dict

        result, stats = inject(
            target_svg,
            # output_dir=tmp_path,
            all_mappings=translations,
            save_result=True,
            return_stats=True,
        )
        assert result is not None
        assert isinstance(stats, dict)
        assert "inserted_translations" in stats

        source_svg = FIXTURES_DIR / "after_translate.svg"
        new_text = target_svg.read_text(encoding="utf-8")
        expected_text = source_svg.read_text(encoding="utf-8")

        assert new_text == expected_text
