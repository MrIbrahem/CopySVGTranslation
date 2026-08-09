# extraction/switch_collector.py
from __future__ import annotations

from ..config import TranslationConfig
from ..core import SwitchNode
from ..core.mapping import TranslationMapping
from ..utils.text import normalize_text
from .strategies import MatchingStrategy


class SwitchTranslationCollector:
    """Collect translations from one <switch> into a TranslationMapping."""

    def __init__(
        self,
        config: TranslationConfig,
        strategy: MatchingStrategy,
    ) -> None:
        self.config = config
        self.strategy = strategy

    def collect(self, switch: SwitchNode, mapping: TranslationMapping) -> None:
        default = switch.default_text_node()
        if default is None:
            return

        default_texts = default.texts(
            normalize=True,
            case_insensitive=self.config.case_insensitive,
        )
        if not any(default_texts):
            return

        for tspan in default.tspans():
            tid = tspan.get("id")
            if tid and tspan.text and tspan.text.strip():
                mapping.tspans_by_id[tid] = tspan.text.strip()

        for x in default_texts:
            key = normalize_text(x, self.config.case_insensitive)
            mapping.new.setdefault(key, {})

        for node in switch.text_nodes():
            if node.is_fallback or not node.language:
                continue

            matches = self.strategy.match(
                default,
                node,
                case_insensitive=self.config.case_insensitive,
            )
            for m in matches:
                key = normalize_text(m.default_text, self.config.case_insensitive)
                mapping.add(
                    key,
                    node.language,
                    m.translated_text,
                    case_insensitive=False,
                )
