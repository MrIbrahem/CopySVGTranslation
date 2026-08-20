"""Output-path resolution helpers for SVG persistence."""

from __future__ import annotations

from pathlib import Path

from ..config import TranslationConfig


def resolve_svg_output_path(output: Path | str, *, config: TranslationConfig) -> Path:
    """Resolve a high-level SVG output path using the configured output directory.

    A bare filename is placed in ``config.output_dir`` when that directory is
    configured. Paths with an explicit parent directory are intentionally kept
    unchanged.
    """
    path = Path(output)
    if path.parent == Path(".") and config.output_dir is not None:
        return config.output_dir / path
    return path


__all__ = ["resolve_svg_output_path"]
