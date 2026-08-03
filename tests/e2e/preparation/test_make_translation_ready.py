"""

pytest tests/preparation/test_preparation.py

"""

from pathlib import Path

from CopySVGTranslation.preparation import make_translation_ready

FIXTURES_DIR = Path(__file__).parent


class TestIntegrationWorkflows:

    def test_make_translation_ready(self, tmp_path):
        svg_new = tmp_path / "before_translate_ready.svg"
        tree, _root = make_translation_ready(FIXTURES_DIR / "before_translate.svg")
        tree.write(str(svg_new), pretty_print=True, xml_declaration=True, encoding="utf-8")
        assert svg_new.exists()
        assert str(tree.getroot().tag).endswith("svg")
