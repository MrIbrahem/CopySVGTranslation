"""Additional comprehensive pytest tests for CopySVGTranslation."""

from pathlib import Path

from CopySVGTranslation.nested.detector import NestedTspanDetector

SVG_NS = "http://www.w3.org/2000/svg"


def _write_svg(tmp_path: Path, content: str) -> Path:
    """Helper to write temporary SVG file."""
    svg_data = f'<svg xmlns="{SVG_NS}">{content}</svg>'
    file_path = tmp_path / "test.svg"
    file_path.write_text(svg_data, encoding="utf-8")
    return file_path


class TestDetectorFindInFile:

    def find_in_file(self, source_file: Path) -> list:
        detector = NestedTspanDetector()
        return detector.find_in_file(source_file)

    def test_returns_empty_if_file_not_exists(self, tmp_path):
        fake_path = tmp_path / "missing.svg"
        result = self.find_in_file(fake_path)
        assert result == []

    def test_returns_empty_if_invalid_svg(self, tmp_path):
        bad_path = tmp_path / "bad.svg"
        bad_path.write_text("<svg><text><tspan></svg>", encoding="utf-8")
        result = self.find_in_file(bad_path)
        assert result == []

    def test_returns_empty_if_no_tspan(self, tmp_path):
        path = _write_svg(tmp_path, "<text>No tspan here</text>")
        result = self.find_in_file(path)
        assert result == []

    def test_returns_empty_if_no_nested_tspan(self, tmp_path):
        path = _write_svg(tmp_path, "<text><tspan>Flat</tspan></text>")
        result = self.find_in_file(path)
        assert result == []

    def test_finds_single_nested_tspan(self, tmp_path):
        path = _write_svg(tmp_path, "<text><tspan>A<tspan>B</tspan></tspan></text>")
        result = self.find_in_file(path)
        assert len(result) == 1
        assert "<tspan" in result[0]
        assert "A" in result[0]
        assert "B" in result[0]

    def test_finds_multiple_nested_tspans(self, tmp_path):
        path = _write_svg(tmp_path, "<text><tspan>X<tspan>Y</tspan></tspan><tspan>P<tspan>Q</tspan></tspan></text>")
        result = self.find_in_file(path)
        assert len(result) == 2
        assert all("<tspan" in r for r in result)

    def test_ignores_non_element_children(self, tmp_path):
        path = _write_svg(tmp_path, "<text><tspan>hello world</tspan></text>")
        result = self.find_in_file(path)
        assert result == []

    def test_handles_empty_root(self, tmp_path):
        path = tmp_path / "empty.svg"
        path.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
        result = self.find_in_file(path)
        assert result == []
