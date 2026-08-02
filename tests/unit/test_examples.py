import json
from pathlib import Path

import pytest

from CopySVGTranslation import extract, inject
from CopySVGTranslation.workflows import svg_extract_and_inject

FIXTURES_DIR = Path(__file__).parent.parent / "tests_files/example"


class TestIntegrationWorkflows:

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Prepare temp directory and input/output files."""
        test_dir = tmp_path
        self.test_dir = test_dir
        self.source_svg = FIXTURES_DIR / "source.svg"
        self.target_svg = test_dir / "before_translate.svg"
        self.output_svg = test_dir / "output.svg"
        self.data_file = test_dir / "data.json"

        # Copy fixture
        self.target_svg.write_text(
            (FIXTURES_DIR / "before_translate.svg").read_text(encoding="utf-8"), encoding="utf-8"
        )

        expected_svg = FIXTURES_DIR / "after_translate.svg"
        self.expected_text = expected_svg.read_text(encoding="utf-8")

    def test_svg_extract_and_inject_end_to_end(self):
        r = svg_extract_and_inject(
            self.source_svg,
            self.target_svg,
            output_file=self.output_svg,
            data_output_file=self.data_file,
            save_result=True,
        )
        assert r is not None
        assert self.output_svg.exists()
        assert self.data_file.exists()

    def test_inject_with_dict(self):
        translations = extract(self.source_svg)
        result, stats = inject(
            self.target_svg,
            output_dir=self.test_dir,
            all_mappings=translations,
            save_result=True,
            return_stats=True,
        )
        assert result is not None
        assert isinstance(stats, dict)
        assert "inserted_translations" in stats

        # new_text = self.target_svg.read_text(encoding="utf-8")
        # assert new_text == self.expected_text

    def test_translations(self):
        new_data_file = FIXTURES_DIR / "data.json"
        translations = extract(self.source_svg)

        with open(new_data_file, "w", encoding="utf-8") as handle:
            json.dump(translations, handle, indent=4, ensure_ascii=False)

        assert translations is not None
        assert isinstance(translations, dict)

    def test_translations_compare(self):
        new_data_file = FIXTURES_DIR / "data.json"
        expected_data_path = FIXTURES_DIR / "expected_data.json"

        new_data = json.loads(new_data_file.read_text(encoding="utf-8"))
        expected_data = json.loads(expected_data_path.read_text(encoding="utf-8"))

        assert new_data_file.exists()
        assert expected_data_path.exists()

        assert new_data["new"] == expected_data["new"]
        assert new_data["title"] == expected_data["title"]
