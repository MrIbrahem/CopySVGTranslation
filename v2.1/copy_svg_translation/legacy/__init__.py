# legacy/__init__.py
from .extract import extract
from .inject import inject_file_tree
from .workflows import svg_extract_and_inject, svg_extract_and_injects

__all__ = [
    "extract",
    "inject_file_tree",
    "svg_extract_and_inject",
    "svg_extract_and_injects",
]
