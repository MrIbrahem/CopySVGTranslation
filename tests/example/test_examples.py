import json
from pathlib import Path

import pytest

from CopySVGTranslation import extract, inject
from CopySVGTranslation.workflows import svg_extract_and_inject

FIXTURES_DIR = Path(__file__).parent


class TestIntegrationWorkflows:

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Prepare temp directory and input/output files."""
        test_dir = tmp_path
        source_svg = FIXTURES_DIR / "source.svg"
        target_svg = test_dir / "before_translate.svg"
        output_svg = test_dir / "output.svg"
        data_file = test_dir / "data.json"

        # Copy fixture
        target_svg.write_text((FIXTURES_DIR / "before_translate.svg").read_text(encoding="utf-8"), encoding="utf-8")

        expected_svg = FIXTURES_DIR / "after_translate.svg"
        expected_text = expected_svg.read_text(encoding="utf-8")

        self.setup_tmpdir = {
            "test_dir": test_dir,
            "source_svg": source_svg,
            "target_svg": target_svg,
            "output_svg": output_svg,
            "data_file": data_file,
            "expected_text": expected_text,
        }

    def test_svg_extract_and_inject_end_to_end(self):
        r = svg_extract_and_inject(
            self.setup_tmpdir["source_svg"],
            self.setup_tmpdir["target_svg"],
            output_file=self.setup_tmpdir["output_svg"],
            data_output_file=self.setup_tmpdir["data_file"],
            save_result=True,
        )
        assert r is not None
        assert self.setup_tmpdir["output_svg"].exists()
        assert self.setup_tmpdir["data_file"].exists()

    def test_inject_with_dict(self):
        translations = extract(self.setup_tmpdir["source_svg"])
        result, stats = inject(
            self.setup_tmpdir["target_svg"],
            output_dir=self.setup_tmpdir["test_dir"],
            all_mappings=translations,
            save_result=True,
            return_stats=True,
        )
        assert result is not None
        assert isinstance(stats, dict)
        assert "inserted_translations" in stats

        # new_text = self.setup_tmpdir["target_svg"].read_text(encoding="utf-8")
        # assert new_text == self.setup_tmpdir["expected_text"]

    def test_translations(self):
        new_data_file = FIXTURES_DIR / "data.json"
        translations = extract(self.setup_tmpdir["source_svg"])

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
