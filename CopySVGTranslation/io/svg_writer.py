"""Shared, atomic persistence helpers for transformed SVG documents."""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path

from lxml import etree

from ..config import TranslationConfig


def write_svg(
    document: etree._ElementTree | etree._Element,
    path: Path | str,
    *,
    config: TranslationConfig,
    pretty_print: bool | None = None,
    create_parents: bool | None = None,
) -> Path:
    """Atomically write an SVG element or tree using the configured policy.

    The writer centralizes the persistence behavior shared by injection,
    preparation, nested-structure repair, and :class:`SvgDocument`. It emits
    UTF-8 XML with a declaration, uses the configured pretty-print policy, and
    optionally creates the destination's parent directories.
    """
    target = Path(path)
    if target.exists() and target.is_dir():
        raise IsADirectoryError(f"SVG output path is a directory: {target}")
    existing_mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else None

    should_create_parents = config.create_parents if create_parents is None else create_parents
    if should_create_parents:
        target.parent.mkdir(parents=True, exist_ok=True)

    resolved_pretty_print = config.pretty_print if pretty_print is None else pretty_print
    resolved_pretty_print = True if resolved_pretty_print is None else resolved_pretty_print
    tree = document if isinstance(document, etree._ElementTree) else etree.ElementTree(document)

    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    temporary_path = Path(temporary_name)

    try:
        if existing_mode is not None:
            os.chmod(temporary_path, existing_mode)
        with os.fdopen(file_descriptor, "wb") as temporary_file:
            tree.write(
                temporary_file,
                encoding="utf-8",
                xml_declaration=True,
                pretty_print=resolved_pretty_print,
            )
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, target)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    return target


__all__ = ["write_svg"]
