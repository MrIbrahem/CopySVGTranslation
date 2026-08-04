# config.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass(slots=True)
class TranslationConfig:
    """
    Central configuration for all SVG translation operations.
    Immutable by convention - create a new instance to change settings.
    """

    # --- Matching / lookup ---
    case_insensitive: bool = True
    """Treat source text keys as case-insensitive (lowercased)."""

    # --- Injection behaviour ---
    overwrite: bool = False
    """If True, update existing language nodes instead of skipping them."""

    pretty_print: bool | None = None
    """Pretty-print the output SVG when saving."""

    # --- Nested tspan handling ---
    nested_strategy: Literal["split_nested_tspans", "flatten", "raise"] = "split_nested_tspans"
    """
    How to handle nested <tspan> (and <a>) elements:
    - split_nested_tspans: convert nested styled tspans into sibling tspans (preferred)
    - flatten: concatenate all text into a single tspan
    - raise: raise an error when nested tspans are found
    """

    # --- Title / year handling ---
    enable_year_titles: bool = True
    """Enable special handling for titles that contain a 4-digit year."""

    # --- I/O behaviour ---
    auto_save: bool = False
    """If True, save results automatically when an output path is available."""

    output_dir: Path | None = None
    """Default directory for output SVGs (used when only a filename is given)."""

    mapping_output_dir: Path | None = None
    """Default directory for extracted JSON mapping files."""

    create_parents: bool = True
    """Create parent directories when saving files."""

    # --- Parsing / preparation ---
    remove_blank_text: bool = True
    """Pass remove_blank_text=True to the XML parser."""

    normalize_languages: bool = True
    """Normalize systemLanguage values (e.g. en_us → en-US)."""

    assign_missing_ids: bool = True
    """Automatically assign trsvgN IDs to translatable nodes that lack an id."""

    # --- Logging / diagnostics ---
    collect_warnings: bool = True
    """Collect non-fatal warnings into OperationResult.warnings."""

    # --- Advanced / future ---
    extra: dict = field(default_factory=dict, repr=False)
    """Escape hatch for experimental or one-off options."""

    def with_updates(self, **kwargs) -> TranslationConfig:
        """Return a new config with the given fields replaced."""
        from dataclasses import replace

        return replace(self, **kwargs)


__all__ = [
    "TranslationConfig",
]
