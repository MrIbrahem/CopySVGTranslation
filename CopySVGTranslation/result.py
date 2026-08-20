"""
TODO: write docs
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from .core.mapping import InjectorStats

TY = TypeVar("TY")


@dataclass(slots=True)
class OperationResult(Generic[TY]):
    success: bool
    data: TY | None = None
    stats: InjectorStats | None = None
    error: str | None = None
    error_code: str | None = None
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def ok(
        cls,
        data: TY,
        stats: InjectorStats | None = None,
        warnings: list[str] | None = None,
    ) -> OperationResult[TY]:
        return cls(
            success=True,
            data=data,
            stats=stats,
            warnings=warnings or [],
        )

    @classmethod
    def fail(
        cls,
        error: str,
        error_code: str | None = None,
        stats: InjectorStats | None = None,
        warnings: list[str] | None = None,
    ) -> OperationResult[TY]:
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            stats=stats,
            warnings=warnings or [],
        )


# Convenience aliases
ExtractResult = OperationResult["TranslationMapping"]  # type: ignore # forward ref
InjectResult = OperationResult["InjectorData"]  # type: ignore # forward ref


__all__ = [
    "OperationResult",
]
