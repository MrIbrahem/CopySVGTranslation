from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RepairResult:
    """
    Statistics and results of a nested structure repair operation.
    """

    success: bool
    len_tags_before_fix: int
    len_tags_after_fix: int
    len_tags_fixed: int = 0
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.len_tags_fixed = max(0, self.len_tags_before_fix - self.len_tags_after_fix)


__all__ = []
