# extraction/strategies.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..core.text_node import TextNode
from ..utils.text import normalize_text

SVG_NS = "http://www.w3.org/2000/svg"


@dataclass(slots=True)
class SegmentMatch:
    """One matched pair: default segment ↔ translated segment."""

    default_text: str
    translated_text: str
    default_id: str | None = None
    translated_id: str | None = None


class MatchingStrategy(ABC):
    """
    How to associate translated <text>/<tspan> content
    with the default (fallback) content inside the same <switch>.
    """

    @abstractmethod
    def match(
        self,
        default_node: TextNode,
        translated_node: TextNode,
        *,
        case_insensitive: bool = True,
    ) -> list[SegmentMatch]:
        """
        Return matched segments for one language node.
        """
        ...


class ByTspanIdStrategy(MatchingStrategy):
    """
    Preferred strategy.

    Assumes translated tspan ids are derived from the default ids:
      trsvg12  →  trsvg12-ar  or  trsvg12_ar  or  ar-trsvg12  etc.
    """

    def match(
        self,
        default_node: TextNode,
        translated_node: TextNode,
        *,
        case_insensitive: bool = True,
    ) -> list[SegmentMatch]:
        default_by_id: dict[str, str] = {}
        for tspan in default_node.tspans():
            tid = tspan.get("id")
            if not tid or not (tspan.text and tspan.text.strip()):
                continue
            base = tid.split("-")[0].split("_")[0].strip()
            text = normalize_text(tspan.text, case_insensitive)
            default_by_id[base] = text
            default_by_id[base.lower()] = text

        matches: list[SegmentMatch] = []
        for tspan in translated_node.tspans():
            tid = tspan.get("id")
            raw = (tspan.text or "").strip()
            if not tid or not raw:
                continue
            base = tid.split("-")[0].split("_")[0].strip()
            default_text = default_by_id.get(base) or default_by_id.get(base.lower())
            if default_text is None:
                continue
            matches.append(
                SegmentMatch(
                    default_text=default_text,
                    translated_text=normalize_text(raw),
                    default_id=base,
                    translated_id=tid,
                )
            )
        return matches


class ByPositionStrategy(MatchingStrategy):
    """
    Fallback strategy when ids are missing or unreliable.
    """

    def match(
        self,
        default_node: TextNode,
        translated_node: TextNode,
        *,
        case_insensitive: bool = True,
    ) -> list[SegmentMatch]:
        default_texts = default_node.texts(normalize=True, case_insensitive=case_insensitive)
        translated_texts = translated_node.texts(
            normalize=True,
            case_insensitive=False,
        )

        matches: list[SegmentMatch] = []
        for i, def_text in enumerate(default_texts):
            if i >= len(translated_texts):
                break
            matches.append(
                SegmentMatch(
                    default_text=def_text,
                    translated_text=translated_texts[i],
                )
            )
        return matches


class CompositeMatchingStrategy(MatchingStrategy):
    """
    Try strategies in order; use the first one that returns any matches.
    """

    def __init__(self, strategies: list[MatchingStrategy] | None = None) -> None:
        self.strategies = strategies or [
            ByTspanIdStrategy(),
            ByPositionStrategy(),
        ]

    def match(
        self,
        default_node: TextNode,
        translated_node: TextNode,
        *,
        case_insensitive: bool = True,
    ) -> list[SegmentMatch]:
        for strategy in self.strategies:
            result = strategy.match(
                default_node,
                translated_node,
                case_insensitive=case_insensitive,
            )
            if result:
                return result
        return []
