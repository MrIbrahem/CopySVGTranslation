import pytest
from pathlib import Path
from CopySvgTranslate import extract, svg_extract_and_inject, inject

FIXTURES_DIR = Path(__file__).parent


@pytest.fixture(autouse=True)
def setup_tmpdir(tmp_path):
    """Prepare temp directory and input/output files."""
    test_dir = tmp_path
    source_svg = FIXTURES_DIR / "source.svg"
    target_svg = test_dir / "before_translate.svg"
    output_svg = test_dir / "output.svg"
    data_file = test_dir / "data.json"

    # Copy fixture
    target_svg.write_text(
        (FIXTURES_DIR / "before_translate.svg").read_text(encoding="utf-8"),
        encoding="utf-8"
    )

    expected_svg = FIXTURES_DIR / "after_translate.svg"
    expected_text = expected_svg.read_text(encoding="utf-8")

    return dict(
        test_dir=test_dir,
        source_svg=source_svg,
        target_svg=target_svg,
        output_svg=output_svg,
        data_file=data_file,
        expected_text=expected_text,
    )


class TestIntegrationWorkflows:
    def test_svg_extract_and_inject_end_to_end(self, setup_tmpdir):
        r = svg_extract_and_inject(
            setup_tmpdir["source_svg"],
            setup_tmpdir["target_svg"],
            output_file=setup_tmpdir["output_svg"],
            data_output_file=setup_tmpdir["data_file"],
            save_result=True,
        )
        assert r is not None
        assert setup_tmpdir["output_svg"].exists()
        assert setup_tmpdir["data_file"].exists()

    def test_inject_with_dict(self, setup_tmpdir):
        translations = extract(setup_tmpdir["source_svg"])
        result, stats = inject(
            setup_tmpdir["target_svg"],
            output_dir=setup_tmpdir["test_dir"],
            all_mappings=translations,
            save_result=True,
            return_stats=True,
        )
        assert result is not None
        assert isinstance(stats, dict)
        assert "inserted_translations" in stats

        # new_text = setup_tmpdir["target_svg"].read_text(encoding="utf-8")
        # assert new_text == setup_tmpdir["expected_text"]
