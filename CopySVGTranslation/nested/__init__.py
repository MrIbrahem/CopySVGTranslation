"""Injection phase helpers for CopySVGTranslation."""

from .detector import NestedTspanDetector
from .fixer import MatchFixNestedTags
from .flattener import NestedTspanFlattener
from .service import NestedStructureService, RepairResult

__all__ = [
    "NestedTspanDetector",
    "NestedTspanFlattener",
    "MatchFixNestedTags",
    "NestedStructureService",
    "RepairResult",
]
