# injection/id_manager.py
from __future__ import annotations


class IdManager:
    """
    Tracks existing IDs and generates unique trsvg ID allocations.
    """

    def __init__(self, existing_ids: set[str] | None = None) -> None:
        self.existing_ids = set(existing_ids) if existing_ids else set()
        self._trsvg_counter = 1

    def register(self, id_: str) -> None:
        self.existing_ids.add(id_)

    def register_many(self, ids: set[str] | list[str]) -> None:
        self.existing_ids.update(ids)

    def allocate_trsvg(self) -> str:
        """Allocate a new unique ``trsvg`` identifier."""

        while f"trsvg{self._trsvg_counter}" in self.existing_ids:
            self._trsvg_counter += 1

        candidate = f"trsvg{self._trsvg_counter}"
        self.existing_ids.add(candidate)
        return candidate

    def allocate_clone(self, base_id: str | None, lang: str) -> str:
        if not base_id:
            return self.allocate_trsvg()

        # Remove existing suffix
        base = base_id.split("-")[0].split("_")[0].strip()
        candidate = f"{base}-{lang.lower()}"
        if candidate not in self.existing_ids:
            self.existing_ids.add(candidate)
            return candidate

        # Handle collisions
        idx = 1
        while True:
            candidate = f"{base}-{lang.lower()}_{idx}"
            idx += 1
            if candidate not in self.existing_ids:
                self.existing_ids.add(candidate)
                return candidate

    def allocate_for_tspan(self, original_id: str | None, lang: str) -> str:
        return self.allocate_clone(original_id, lang)


__all__ = [
    "IdManager",
]
