"""Additional comprehensive pytest tests for CopySVGTranslation."""

from CopySVGTranslation.legacy import inject_file_tree
from CopySVGTranslation.legacy.extract import extract

# -------------------------------
# Preparation function tests
# -------------------------------


# -------------------------------
# Workflow tests
# -------------------------------


class TestWorkflowFunctions:
    """Tests for high-level workflow functions."""

    def test_inject_basic_workflow(self, temp_dir):
        """Test basic inject workflow."""
        target = temp_dir / "target.svg"
        content = """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t1"><tspan>Hi</tspan></text></switch></svg>"""
        target.write_text(content, encoding="utf-8")

        translations = {"new": {"hi": {"ar": "مرحبا"}}}

        tree, stats = inject_file_tree(
            mapping=translations,
            inject_file=target,
            return_stats=True,
            save_result=True,
        )

        assert tree is not None
        assert stats is not None


# -------------------------------
# Extraction edge cases
# -------------------------------


class TestExtractorEdgeCases:
    """Edge case tests for extraction."""

    def test_extract_multiple_languages(self, temp_dir):
        """Test extracting with multiple language translations."""
        svg = temp_dir / "test.svg"
        content = """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch>
<text id="t-ar" systemLanguage="ar"><tspan id="s-ar">مرحبا</tspan></text>
<text id="t-fr" systemLanguage="fr"><tspan id="s-fr">Bonjour</tspan></text>
<text id="t"><tspan id="s">Hello</tspan></text></switch></svg>"""
        svg.write_text(content, encoding="utf-8")
        result = extract(svg)
        assert result is not None
        assert "new" in result
        assert result == {
            "new": {"hello": {"ar": "مرحبا", "fr": "Bonjour"}},
            "tspans_by_id": {"s": "Hello"},
            "title_new": {},
            "error": "",
            "meta": {},
        }

    def test_extract_empty_svg_gracefully(self, temp_dir):
        """Test extract handles empty SVG gracefully."""
        svg = temp_dir / "empty.svg"
        svg.write_text('<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"></svg>', encoding="utf-8")
        result = extract(svg)
        assert result is None



# -------------------------------
# Injection edge cases
# -------------------------------


class TestInjectionEdgeCases:
    """Edge case tests for injection."""

    def test_inject_with_save_path(self, temp_dir):
        """Test inject saves to specified output directory."""
        svg = temp_dir / "test.svg"
        out_dir = temp_dir / "out"
        out_dir.mkdir()
        content = """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hi</tspan></text></switch></svg>"""
        svg.write_text(content, encoding="utf-8")
        mappings = {"new": {"hi": {"ar": "مرحبا"}}}
        tree = inject_file_tree(
            inject_file=svg,
            mapping=mappings,
            save_path=out_dir / "test.svg",
        )
        assert tree is not None
        assert (out_dir / "test.svg").exists()

    def test_inject_case_sensitive_mode(self, temp_dir):
        """Test inject in case-sensitive mode."""
        svg = temp_dir / "test.svg"
        content = """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hello</tspan></text></switch></svg>"""
        svg.write_text(content, encoding="utf-8")
        mappings = {"new": {"Hello": {"ar": "مرحبا"}}}
        tree, stats = inject_file_tree(
            inject_file=svg,
            mapping=mappings,
            case_insensitive=False,
            return_stats=True,
        )
        assert tree is not None
        assert stats is not None
