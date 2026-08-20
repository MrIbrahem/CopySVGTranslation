"""Regression tests for the shared SVG persistence policy."""

from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.io.svg_writer import write_svg

SVG_NS = "http://www.w3.org/2000/svg"


def _tree(text: str = "مرحبا") -> etree._ElementTree:
    root = etree.fromstring(f'<svg xmlns="{SVG_NS}"><text>{text}</text></svg>'.encode())
    return etree.ElementTree(root)


def test_write_svg_creates_parents_and_emits_utf8_declaration(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "output" / "translated.svg"

    written = write_svg(_tree(), target, config=TranslationConfig(create_parents=True))

    assert written == target
    assert target.exists()
    content = target.read_bytes()
    assert content.startswith(b"<?xml")
    assert b"encoding='utf-8'" in content.lower()
    assert "مرحبا" in content.decode("utf-8")
    assert etree.parse(str(target)).getroot().tag == f"{{{SVG_NS}}}svg"


def test_write_svg_respects_disabled_parent_creation(tmp_path: Path) -> None:
    target = tmp_path / "missing" / "translated.svg"

    with pytest.raises(FileNotFoundError):
        write_svg(_tree(), target, config=TranslationConfig(create_parents=False))

    assert not target.exists()


def test_write_svg_accepts_root_and_atomically_replaces_existing_file(tmp_path: Path) -> None:
    target = tmp_path / "translated.svg"
    target.write_text("old content", encoding="utf-8")
    root = _tree("updated").getroot()

    write_svg(root, target, config=TranslationConfig(pretty_print=False))

    content = target.read_text(encoding="utf-8")
    assert "old content" not in content
    assert "updated" in content
    assert content.startswith("<?xml")
    assert list(tmp_path.glob(f".{target.name}.*.tmp")) == []


def test_write_svg_rejects_directory_target(tmp_path: Path) -> None:
    destination = tmp_path / "directory"
    destination.mkdir()

    with pytest.raises(IsADirectoryError, match="directory"):
        write_svg(_tree(), destination, config=TranslationConfig())
