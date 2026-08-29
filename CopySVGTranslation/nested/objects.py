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

    @classmethod
    def ok(
        cls,
        len_before: int,
        len_after: int,
    ) -> RepairResult:
        return cls(
            success=True,
            len_tags_before_fix=len_before,
            len_tags_after_fix=len_after,
        )

    @classmethod
    def fail(cls, warnings: list[str]) -> RepairResult:
        return cls(
            success=False,
            len_tags_before_fix=0,
            len_tags_after_fix=0,
            warnings=warnings,
        )
__all__ = []
