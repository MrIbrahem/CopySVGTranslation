# injection/translation_applier.py
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Literal

from lxml import etree

from ..config import TranslationConfig
from .id_manager import IdManager

SVG_NS = "http://www.w3.org/2000/svg"


@dataclass
class ApplyResult:
    action: Literal["inserted", "updated", "skipped"]
    node: etree._Element | None = None  # new or updated node


class TranslationApplier:
    def __init__(self, config: TranslationConfig, id_manager: IdManager) -> None:
        self.config = config
        self.id_manager = id_manager

    def apply_language(
        self,
        default_node: etree._Element,
        default_texts: list[str],
        lang: str,
        translations: dict[str, str],  # source -> translated for each segment
        existing_lang_node: etree._Element | None,
    ) -> ApplyResult:
        """
        - If existing_lang_node and not overwrite -> skipped
        - If existing_lang_node and overwrite -> update tspans in place
        - Else -> clone default_node, set systemLanguage, fill translations, new IDs
        """
        if existing_lang_node is not None:
            if not self.config.overwrite:
                return ApplyResult(action="skipped", node=existing_lang_node)

            # Update tspans in place
            tspans = existing_lang_node.xpath("./svg:tspan", namespaces={"svg": SVG_NS})
            if tspans:
                for i, tspan in enumerate(tspans):
                    if i < len(default_texts):
                        source = default_texts[i]
                        translated = translations.get(source)
                        if translated is not None:
                            tspan.text = translated
            else:
                source = default_texts[0] if default_texts else ""
                translated = translations.get(source)
                if translated is not None:
                    existing_lang_node.text = translated

            return ApplyResult(action="updated", node=existing_lang_node)

        # Clone default node
        cloned = copy.deepcopy(default_node)
        cloned.set("systemLanguage", lang)

        # Reassign IDs for the cloned node hierarchy
        self._reassign_ids(cloned, lang)

        # Fill translations
        tspans = cloned.xpath("./svg:tspan", namespaces={"svg": SVG_NS})
        if tspans:
            for i, tspan in enumerate(tspans):
                if i < len(default_texts):
                    source = default_texts[i]
                    translated = translations.get(source)
                    if translated is not None:
                        tspan.text = translated
        else:
            source = default_texts[0] if default_texts else ""
            translated = translations.get(source)
            if translated is not None:
                cloned.text = translated

        return ApplyResult(action="inserted", node=cloned)

    def _reassign_ids(self, element: etree._Element, lang: str) -> None:
        old_id = element.get("id")
        if old_id:
            new_id = self.id_manager.allocate_clone(old_id, lang)
            element.set("id", new_id)

        # Recursively update children
        for child in element:
            self._reassign_ids(child, lang)


__all__ = [
    "ApplyResult",
    "TranslationApplier",
]
