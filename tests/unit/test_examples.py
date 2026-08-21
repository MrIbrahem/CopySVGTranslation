import json

import pytest

from CopySVGTranslation import SVGTranslationService


class TestIntegrationWorkflows:

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path, fixtures_dir):
        """Prepare temp directory and input/output files."""
        test_dir = tmp_path
        self.fixtures_dir = fixtures_dir / "example"

        if not self.fixtures_dir.exists():
            pytest.skip("Example files not found")

        self.test_dir = test_dir
        self.source_svg = self.fixtures_dir / "source.svg"
        self.target_svg = test_dir / "before_translate.svg"
        self.output_svg = test_dir / "output.svg"
        self.data_file = test_dir / "data.json"

        # Copy fixture
        self.target_svg.write_text(
            (self.fixtures_dir / "before_translate.svg").read_text(encoding="utf-8"), encoding="utf-8"
        )

        expected_svg = self.fixtures_dir / "after_translate.svg"
        self.expected_text = expected_svg.read_text(encoding="utf-8")

    def test_inject_with_dict(self):
        service = SVGTranslationService()
        _extract_result = service.extract(self.source_svg)
        assert _extract_result.success

        result = service.inject(
            svg_path=self.target_svg,
            mapping=_extract_result.data,
            output=self.test_dir / "t.svg",
            save=True,
        )
        assert result.success
        assert result.data is not None
        stats = result.data.inject_stats.to_json()
        assert isinstance(stats, dict)
        assert "inserted_translations" in stats

        # new_text = self.target_svg.read_text(encoding="utf-8")
        # assert new_text == self.expected_text

    def test_translations(self):
        new_data_file = self.fixtures_dir / "data.json"
        service = SVGTranslationService()
        _result = service.extract(self.source_svg)
        assert _result.success
        assert _result.data is not None
        translations = _result.data.to_json()

        with open(new_data_file, "w", encoding="utf-8") as handle:
            json.dump(translations, handle, indent=4, ensure_ascii=False)

        assert translations is not None
        assert isinstance(translations, dict)

    def test_translations_compare(self):
        new_data_file = self.fixtures_dir / "data.json"
        expected_data_path = self.fixtures_dir / "expected_data.json"
        if not expected_data_path.exists():
            pytest.skip("Example files not found")

        new_data = json.loads(new_data_file.read_text(encoding="utf-8"))
        expected_data = json.loads(expected_data_path.read_text(encoding="utf-8"))

        assert new_data_file.exists()
        assert expected_data_path.exists()

        assert new_data["new"] == expected_data["new"]
