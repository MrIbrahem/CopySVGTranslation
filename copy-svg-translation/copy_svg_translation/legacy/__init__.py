# legacy/__init__.py
from .extract import extract
from .inject import inject
from .workflows import svg_extract_and_inject, svg_extract_and_injects

__all__ = [
    "extract",
    "inject",
    "svg_extract_and_inject",
    "svg_extract_and_injects",
]
