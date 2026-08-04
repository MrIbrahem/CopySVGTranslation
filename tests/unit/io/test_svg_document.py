"""
Unit tests for CopySVGTranslation/io/svg_document.py module.

Classes to test: SvgDocument
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from lxml import etree

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.exceptions import SvgStructureError
from CopySVGTranslation.io.svg_document import SvgDocument

SVG_NS = "http://www.w3.org/2000/svg"


def _write_svg(tmp_path: Path, content: str, name: str = "test.svg") -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
class TestSvgDocumentLoad:
    """Tests for SvgDocument.load."""

    def test_load_valid_svg(self, tmp_path: Path):
        svg = _write_svg(
            tmp_path,
            f"""
            <svg xmlns="{SVG_NS}">
                <text>Hello</text>
            </svg>
            """,
        )
        doc = SvgDocument.load(svg)
        assert doc.root is not None
        assert doc.path == svg

    def test_load_file_not_found(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            SvgDocument.load(tmp_path / "missing.svg")

    def test_load_invalid_xml(self, tmp_path: Path):
        svg = _write_svg(tmp_path, "not xml <><>")
        with pytest.raises(etree.XMLSyntaxError):
            SvgDocument.load(svg)

    def test_load_with_config(self, tmp_path: Path):
        svg = _write_svg(tmp_path, f'<svg xmlns="{SVG_NS}"></svg>')
        config = TranslationConfig(remove_blank_text=False)
        doc = SvgDocument.load(svg, config=config)
        assert doc.config.remove_blank_text is False

    def test_load_string_path(self, tmp_path: Path):
        svg = _write_svg(tmp_path, f'<svg xmlns="{SVG_NS}"></svg>')
        doc = SvgDocument.load(str(svg))
        assert doc.root is not None

    def test_load_ensures_namespace(self, tmp_path: Path):
        """SVG without namespace should get one assigned via xmlns attribute."""
        svg = _write_svg(tmp_path, "<svg></svg>")
        doc = SvgDocument.load(svg)
        # _ensure_namespace sets the xmlns attribute directly
        xmlns_attr = doc.root.get("{http://www.w3.org/2000/xmlns/}xmlns")
        assert xmlns_attr == SVG_NS


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------
class TestSvgDocumentConstruction:
    """Tests for SvgDocument constructor."""

    def test_constructor_with_tree(self):
        root = etree.Element(f"{{{SVG_NS}}}svg")
        tree = etree.ElementTree(root)
        doc = SvgDocument(tree)
        assert doc.root is root
        assert doc.path is None

    def test_constructor_none_root_raises(self):
        """An ElementTree with a None root should raise SvgStructureError."""
        # Create a tree with no root
        tree = etree.ElementTree()
        with pytest.raises(SvgStructureError):
            SvgDocument(tree)


# ---------------------------------------------------------------------------
# Namespace helper
# ---------------------------------------------------------------------------
class TestSvgDocumentNamespace:
    """Tests for _ensure_namespace."""

    def test_adds_namespace_when_missing(self):
        root = etree.Element("svg")
        tree = etree.ElementTree(root)
        doc = SvgDocument(tree)
        # _ensure_namespace sets xmlns attribute when nsmap has no default ns
        xmlns = root.get("{http://www.w3.org/2000/xmlns/}xmlns")
        # If nsmap was None, xmlns attr should now be set
        assert xmlns == SVG_NS or root.nsmap.get(None) == SVG_NS

    def test_preserves_existing_namespace(self):
        root = etree.Element(f"{{{SVG_NS}}}svg")
        root.set("{http://www.w3.org/2000/xmlns/}xmlns", SVG_NS)
        tree = etree.ElementTree(root)
        doc = SvgDocument(tree)
        assert root.get("{http://www.w3.org/2000/xmlns/}xmlns") == SVG_NS


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
class TestSvgDocumentSave:
    """Tests for SvgDocument.save."""

    def test_save_to_provided_path(self, tmp_path: Path):
        root = etree.Element(f"{{{SVG_NS}}}svg")
        child = etree.SubElement(root, f"{{{SVG_NS}}}text")
        child.text = "Hello"
        tree = etree.ElementTree(root)
        doc = SvgDocument(tree, path=tmp_path / "original.svg")

        out = tmp_path / "saved.svg"
        result = doc.save(out)
        assert result == out
        assert out.exists()

    def test_save_to_original_path(self, tmp_path: Path):
        svg_path = _write_svg(tmp_path, f'<svg xmlns="{SVG_NS}"><text>Hi</text></svg>')
        doc = SvgDocument.load(svg_path)
        result = doc.save()
        assert result == svg_path

    def test_save_no_path_raises(self):
        root = etree.Element(f"{{{SVG_NS}}}svg")
        tree = etree.ElementTree(root)
        doc = SvgDocument(tree)
        with pytest.raises(ValueError, match="No target path"):
            doc.save()

    def test_save_creates_parents(self, tmp_path: Path):
        root = etree.Element(f"{{{SVG_NS}}}svg")
        tree = etree.ElementTree(root)
        out = tmp_path / "sub" / "dir" / "file.svg"
        doc = SvgDocument(tree, config=TranslationConfig(create_parents=True))
        doc.save(out)
        assert out.exists()

    def test_save_no_create_parents(self, tmp_path: Path):
        root = etree.Element(f"{{{SVG_NS}}}svg")
        tree = etree.ElementTree(root)
        out = tmp_path / "nonexistent" / "file.svg"
        doc = SvgDocument(tree, config=TranslationConfig(create_parents=False))
        with pytest.raises((FileNotFoundError, OSError)):
            doc.save(out)

    def test_save_pretty_print_override(self, tmp_path: Path):
        root = etree.Element(f"{{{SVG_NS}}}svg")
        tree = etree.ElementTree(root)
        out = tmp_path / "pp.svg"
        doc = SvgDocument(tree)
        doc.save(out, pretty_print=False)
        assert out.exists()

    def test_save_create_parents_override(self, tmp_path: Path):
        root = etree.Element(f"{{{SVG_NS}}}svg")
        tree = etree.ElementTree(root)
        out = tmp_path / "a" / "b" / "file.svg"
        doc = SvgDocument(tree, config=TranslationConfig(create_parents=False))
        doc.save(out, create_parents=True)
        assert out.exists()


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------
class TestSvgDocumentQuery:
    """Tests for xpath and findall convenience methods."""

    def test_xpath(self):
        root = etree.Element(f"{{{SVG_NS}}}svg")
        text = etree.SubElement(root, f"{{{SVG_NS}}}text")
        text.text = "Hello"
        tree = etree.ElementTree(root)
        doc = SvgDocument(tree)

        result = doc.xpath("//svg:text")
        assert len(result) == 1
        assert result[0].text == "Hello"

    def test_findall(self):
        root = etree.Element(f"{{{SVG_NS}}}svg")
        etree.SubElement(root, f"{{{SVG_NS}}}text").text = "A"
        etree.SubElement(root, f"{{{SVG_NS}}}text").text = "B"
        etree.SubElement(root, f"{{{SVG_NS}}}rect")
        tree = etree.ElementTree(root)
        doc = SvgDocument(tree)

        texts = doc.findall("text")
        assert len(texts) == 2

    def test_findall_empty(self):
        root = etree.Element(f"{{{SVG_NS}}}svg")
        tree = etree.ElementTree(root)
        doc = SvgDocument(tree)
        assert doc.findall("text") == []
