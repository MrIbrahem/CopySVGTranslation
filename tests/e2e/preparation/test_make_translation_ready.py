"""

pytest tests/preparation/test_preparation.py

"""

from pathlib import Path

import pytest
from lxml import etree

from CopySVGTranslation import TranslationConfig
from CopySVGTranslation.preparation import SvgPreparationPipeline


def preparer_run(source_file: Path | str) -> tuple[etree._ElementTree, etree._Element]:
    """
    unction-style wrapper around SvgPreparationPipeline, kept for
    backward compatibility with existing callers.
    """
    config = TranslationConfig(
        nested_strategy="raise",
    )
    preparer = SvgPreparationPipeline(config)
    return preparer.run(path=source_file)


class TestIntegrationWorkflows:

    def test_make_translation_ready(self, tmp_path, fixtures_dir):
        file = fixtures_dir / "preparation/before_translate.svg"
        if not file.exists():
            pytest.skip("File not found")

        svg_new = tmp_path / "before_translate_ready.svg"
        tree, _root = preparer_run(file)
        tree.write(str(svg_new), pretty_print=True, xml_declaration=True, encoding="utf-8")
        assert svg_new.exists()
        assert str(tree.getroot().tag).endswith("svg")
