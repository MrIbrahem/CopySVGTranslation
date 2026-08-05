"""

pytest tests/preparation/test_preparation.py

"""
import pytest

from CopySVGTranslation.preparation import make_translation_ready

class TestIntegrationWorkflows:

    def test_make_translation_ready(self, tmp_path, fixtures_dir):
        file = fixtures_dir / "preparation/before_translate.svg"
        if not file.exists():
            pytest.skip("File not found")

        svg_new = tmp_path / "before_translate_ready.svg"
        tree, _root = make_translation_ready(file)
        tree.write(str(svg_new), pretty_print=True, xml_declaration=True, encoding="utf-8")
        assert svg_new.exists()
        assert str(tree.getroot().tag).endswith("svg")
