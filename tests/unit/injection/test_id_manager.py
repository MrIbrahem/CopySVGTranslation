"""
Unit tests for CopySVGTranslation/injection/id_manager.py module.

Classes to test: IdManager
"""


from CopySVGTranslation.injection.id_manager import (
    IdManager,
)

def allocate_clone(base_id: str | None, lang: str, existing_ids) -> str:
    id_manager = IdManager(existing_ids)
    return id_manager.allocate_clone(base_id, lang)

class TestGenerateUniqueIdFunction:
    """Comprehensive tests for the allocate_clone function."""

    def test_allocate_clone_no_collision(self):
        """allocate_clone should append language code when no collision."""
        existing_ids = {"id1", "id2"}
        result = allocate_clone("base", "fr", existing_ids)
        assert result == "base-fr"

    def test_allocate_clone_with_collision(self):
        """allocate_clone should handle ID collisions."""
        existing_ids = {"base-ar"}
        result = allocate_clone("base", "ar", existing_ids)
        assert result == "base-ar_1"

    def test_allocate_clone_multiple_collisions(self):
        """allocate_clone should handle multiple collisions."""
        existing_ids = {"base-ar", "base-ar_1", "base-ar_2"}
        result = allocate_clone("base", "ar", existing_ids)
        assert result == "base-ar_3"

    def test_allocate_clone_empty_existing_set(self):
        """allocate_clone should work with empty existing ID set."""
        result = allocate_clone("base", "de", set())
        assert result == "base-de"

    def test_allocate_clone_preserves_base_id(self):
        """allocate_clone should preserve the base ID structure."""
        existing_ids = {"other-id"}
        result = allocate_clone("my-element", "es", existing_ids)
        assert result == "my-es"

    def test_allocate_clone_different_languages(self):
        """allocate_clone should handle different language codes."""
        existing_ids = set()

        ar_id = allocate_clone("base", "ar", existing_ids)
        existing_ids.add(ar_id)

        fr_id = allocate_clone("base", "fr", existing_ids)
        existing_ids.add(fr_id)

        assert ar_id == "base-ar"
        assert fr_id == "base-fr"
        assert ar_id != fr_id

    def test_allocate_clone_complex_base_id(self):
        """allocate_clone should handle complex base IDs."""
        existing_ids = set()
        result = allocate_clone("text-2205-tspan", "ar", existing_ids)
        assert result == "text-ar"

    def test_allocate_clone_idempotency(self):
        """allocate_clone should generate consistent IDs."""
        existing_ids = {"base-ar"}
        result1 = allocate_clone("base", "ar", existing_ids)
        result2 = allocate_clone("base", "ar", existing_ids)
        assert result1 == result2 == "base-ar_1"

    def test_allocate_clone_with_large_collision_set(self):
        """allocate_clone should handle large sets of existing IDs."""
        existing_ids = {f"base-ar_{i}" for i in range(100)}
        existing_ids.add("base-ar")

        result = allocate_clone("base", "ar", existing_ids)
        assert result == "base-ar_100"

    def test_allocate_clone_is_importable(self):
        """The allocate_clone function should be importable from top-level module."""
        assert callable(allocate_clone)
        assert allocate_clone.__name__ == "allocate_clone"


class TestGenerateUniqueId:
    """Tests for injection-related functions."""

    def test_allocate_clone_no_collision(self):
        """Test unique ID generation without collision."""
        result = allocate_clone("text", "ar", {"other"})
        assert result == "text-ar"

    def test_allocate_clone_with_collision(self):
        """Test unique ID generation handles collisions."""
        existing = {"text-ar", "text-ar_1"}
        result = allocate_clone("text", "ar", existing)
        assert result == "text-ar_2"

    def test_allocate_clone_with_many_collisions(self):
        """Test unique ID generation with many existing IDs."""
        existing = {f"id-ar_{i}" for i in range(100)}
        existing.add("id-ar")
        result = allocate_clone("id-ar", "ar", existing)
        assert result == "id-ar_100"

    def test_allocate_clone_empty_base(self):
        """Test unique ID generation with empty base ID."""
        result = allocate_clone("", "ar", set())
        assert result == "trsvg1"

    def test_allocate_clone_with_special_characters(self):
        """Test unique ID generation with special characters in base."""
        result = allocate_clone("text-123", "fr", set())
        assert result == "text-fr"

