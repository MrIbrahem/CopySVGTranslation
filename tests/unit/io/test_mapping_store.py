"""
Unit tests for CopySVGTranslation/io/mapping_store.py module.

Classes to test: MappingStore
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.core.mapping import TranslationMapping
from CopySVGTranslation.io.mapping_store import MappingStore


@pytest.fixture
def store() -> MappingStore:
    return MappingStore()


@pytest.fixture
def sample_mapping() -> TranslationMapping:
    return TranslationMapping(
        new={
            "hello": {"ar": "مرحبا", "fr": "bonjour"},
            "world": {"ar": "عالم", "fr": "monde"},
        },
        title_new={"Some title {year}": {"ar": "عنوان {year}"}},
        tspans_by_id={"t0": "hello"},
    )


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
class TestMappingStoreLoad:
    """Tests for MappingStore.load."""

    def test_load_valid_file(self, tmp_path: Path, store: MappingStore):
        data = {"new": {"hello": {"ar": "مرحبا"}}, "title_new": {}}
        f = tmp_path / "mapping.json"
        f.write_text(json.dumps(data), encoding="utf-8")

        mapping = store.load(f)
        assert isinstance(mapping, TranslationMapping)
        assert "hello" in mapping.new
        assert mapping.new["hello"]["ar"] == "مرحبا"

    def test_load_file_not_found(self, tmp_path: Path, store: MappingStore):
        with pytest.raises(FileNotFoundError):
            store.load(tmp_path / "missing.json")

    def test_load_preserves_all_sections(self, tmp_path: Path, store: MappingStore):
        data = {
            "new": {"text": {"ar": "نص"}},
            "title_new": {"t {year}": {"ar": "ع {year}"}},
            "tspans_by_id": {"t1": "text"},
        }
        f = tmp_path / "full.json"
        f.write_text(json.dumps(data), encoding="utf-8")

        mapping = store.load(f)
        assert "text" in mapping.new
        assert "t {year}" in mapping.title_new
        assert mapping.tspans_by_id["t1"] == "text"

    def test_load_string_path(self, tmp_path: Path, store: MappingStore):
        data = {"new": {"x": {"ar": "y"}}}
        f = tmp_path / "m.json"
        f.write_text(json.dumps(data), encoding="utf-8")

        mapping = store.load(str(f))
        assert "x" in mapping.new


# ---------------------------------------------------------------------------
# Load many
# ---------------------------------------------------------------------------
class TestMappingStoreLoadMany:
    """Tests for MappingStore.load_many."""

    def test_load_many_merges(self, tmp_path: Path, store: MappingStore):
        f1 = tmp_path / "a.json"
        f2 = tmp_path / "b.json"
        f1.write_text(json.dumps({"new": {"hello": {"ar": "مرحبا"}}}), encoding="utf-8")
        f2.write_text(json.dumps({"new": {"world": {"fr": "monde"}}}), encoding="utf-8")

        mapping = store.load_many([f1, f2])
        assert "hello" in mapping.new
        assert "world" in mapping.new

    def test_load_many_skips_missing(self, tmp_path: Path, store: MappingStore):
        f1 = tmp_path / "a.json"
        f1.write_text(json.dumps({"new": {"hello": {"ar": "مرحبا"}}}), encoding="utf-8")

        mapping = store.load_many([f1, tmp_path / "missing.json"])
        assert "hello" in mapping.new

    def test_load_many_empty_list(self, store: MappingStore):
        mapping = store.load_many([])
        assert mapping.is_empty()

    def test_load_many_handles_bad_json(self, tmp_path: Path, store: MappingStore):
        f1 = tmp_path / "good.json"
        f2 = tmp_path / "bad.json"
        f1.write_text(json.dumps({"new": {"x": {"ar": "y"}}}), encoding="utf-8")
        f2.write_text("not json", encoding="utf-8")

        mapping = store.load_many([f1, f2])
        assert "x" in mapping.new  # good one still loaded


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
class TestMappingStoreSave:
    """Tests for MappingStore.save."""

    def test_save_creates_file(self, tmp_path: Path, store: MappingStore, sample_mapping: TranslationMapping):
        out = tmp_path / "output.json"
        result = store.save(sample_mapping, out)

        assert result == out
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "hello" in data["new"]

    def test_save_creates_parent_dirs(self, tmp_path: Path, sample_mapping: TranslationMapping):
        store = MappingStore(TranslationConfig(create_parents=True))
        out = tmp_path / "sub" / "dir" / "output.json"
        store.save(sample_mapping, out)
        assert out.exists()

    def test_save_no_create_parents(self, tmp_path: Path, sample_mapping: TranslationMapping):
        store = MappingStore(TranslationConfig(create_parents=False))
        out = tmp_path / "nonexistent" / "output.json"
        with pytest.raises((FileNotFoundError, OSError)):
            store.save(sample_mapping, out)

    def test_save_roundtrip(self, tmp_path: Path, store: MappingStore, sample_mapping: TranslationMapping):
        out = tmp_path / "rt.json"
        store.save(sample_mapping, out)
        loaded = store.load(out)
        assert loaded.new == sample_mapping.new
        assert loaded.title_new == sample_mapping.title_new
        assert loaded.tspans_by_id == sample_mapping.tspans_by_id

    def test_save_with_indent(self, tmp_path: Path, store: MappingStore, sample_mapping: TranslationMapping):
        out = tmp_path / "indented.json"
        store.save(sample_mapping, out, indent=4)
        content = out.read_text(encoding="utf-8")
        # 4-space indentation should be present
        assert "    " in content

    def test_save_ensure_ascii_false(self, tmp_path: Path, store: MappingStore):
        mapping = TranslationMapping(new={"hi": {"ar": "مرحبا"}})
        out = tmp_path / "unicode.json"
        store.save(mapping, out)
        content = out.read_text(encoding="utf-8")
        # Arabic should be stored directly, not escaped
        assert "مرحبا" in content

    def test_save_string_path(self, tmp_path: Path, store: MappingStore, sample_mapping: TranslationMapping):
        out = tmp_path / "str_path.json"
        store.save(sample_mapping, str(out))
        assert out.exists()

    def test_save_create_parents_override(self, tmp_path: Path, sample_mapping: TranslationMapping):
        store = MappingStore(TranslationConfig(create_parents=False))
        out = tmp_path / "a" / "b" / "output.json"
        # Override create_parents in the save call
        store.save(sample_mapping, out, create_parents=True)
        assert out.exists()


# ---------------------------------------------------------------------------
# default_mapping_path
# ---------------------------------------------------------------------------
class TestDefaultMappingPath:
    """Tests for MappingStore.default_mapping_path."""

    def test_default_path_uses_svg_parent(self, store: MappingStore):
        svg_path = Path("/some/dir/image.svg")
        result = store.default_mapping_path(svg_path)
        assert result.name == "image.svg.json"
        assert "data" in str(result)

    def test_default_path_uses_config_dir(self):
        config = TranslationConfig(mapping_output_dir=Path("/output/maps"))
        store = MappingStore(config)
        svg_path = Path("/some/dir/image.svg")
        result = store.default_mapping_path(svg_path)
        assert result.parent == Path("/output/maps")
        assert result.name == "image.svg.json"
