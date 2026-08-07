# injection/translation_applier.py
from __future__ import annotations

import copy
import logging
from dataclasses import dataclass
from typing import Literal

from lxml import etree

from ..core.text_node import TextNode
from ..config import TranslationConfig
from .id_manager import IdManager

logger = logging.getLogger(__name__)

SVG_NS = "http://www.w3.org/2000/svg"


@dataclass
class ApplyResult:
    action: Literal["inserted", "updated", "unchanged", "skipped"]
    node: etree._Element | None = None  # new or updated node
    text_node: TextNode | None = None


class TranslationApplier:
    def __init__(self, config: TranslationConfig, id_manager: IdManager) -> None:
        self.config = config
        self.id_manager = id_manager

    def _create_node(
        self,
        default_node: TextNode,
        default_texts: list[str],
        lang: str,
        translations: dict[str, str],
    ) -> TextNode:
        cloned = default_node.clone()

        new_node = etree.Element(default_node.element.tag, attrib=default_node.element.attrib)
        new_node.set("systemLanguage", lang)

        # Fill translations
        tspans = cloned.tspans()
        if tspans:
            for i, tspan in enumerate(tspans):
                if i < len(default_texts):
                    source = default_texts[i]
                    translated = translations.get(source)
                    if self._is_translation_valid(translated, tspan.text):
                        tspan.text = translated
                        new_node.append(tspan)
                    elif self.config.fallback_to_default_text:
                        new_node.append(tspan)

        else:
            source = default_texts[0] if default_texts else ""
            translated = translations.get(source)
            if self._is_translation_valid(translated, new_node.text):
                new_node.text = translated

        # Reassign IDs for the cloned node hierarchy
        self._reassign_ids(new_node, lang)

        return TextNode(new_node)

    def _is_translation_valid(self, translated: None | str, tspan_text: str) -> bool:
        valid = translated is not None and translated.strip() != ""
        return valid and tspan_text != translated

    def _reassign_ids(self, element: etree._Element, lang: str) -> None:
        old_id = element.get("id")
        if old_id:
            new_id = self.id_manager.allocate_clone(old_id, lang)
            element.set("id", new_id)

        # Recursively update children
        for child in element:
            self._reassign_ids(child, lang)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply_language_node(
        self,
        default_node: TextNode,
        default_texts: list[str],
        lang: str,
        translations: dict[str, str],  # source -> translated for each segment
        existing_lang_node: TextNode | None,
    ) -> ApplyResult:
        """
        - If existing_lang_node and not overwrite -> skipped
        - If existing_lang_node and overwrite -> update tspans in place
        - Else -> clone default_node, set systemLanguage, fill translations, new IDs
        """
        if existing_lang_node is not None:
            if not self.config.overwrite:
                return ApplyResult(action="skipped", text_node=existing_lang_node)

            # Update tspans in place
            tspans = existing_lang_node.tspans()
            if tspans:
                for i, tspan in enumerate(tspans):
                    if i < len(default_texts):
                        source = default_texts[i]
                        translated = translations.get(source)
                        if not self._is_translation_valid(translated, tspan.text):
                            continue
                        tspan.text = translated
            else:
                source = default_texts[0] if default_texts else ""
                translated = translations.get(source)
                if self._is_translation_valid(translated, existing_lang_node.text):
                    existing_lang_node.text = translated

            return ApplyResult(action="updated", node=existing_lang_node)

        # Clone default node
        cloned = self._create_node(default_node, default_texts, lang, translations)

        return ApplyResult(action="inserted", text_node=cloned)

    def apply_language(
        self,
        default_node: etree._Element,
        default_texts: list[str],
        lang: str,
        translations: dict[str, str],  # source -> translated for each segment
        existing_lang_node: etree._Element | None,
    ) -> ApplyResult:
        """
        Alias
        """
        default = TextNode.from_any(default_node)
        existing_node = TextNode.from_any_or_none(existing_lang_node)

        res = self.apply_language_node(
            default_node=default,
            default_texts=default_texts,
            lang=lang,
            translations=translations,
            existing_lang_node=existing_node,
        )

        element = res.text_node.element if res.text_node else None
        return ApplyResult(action=res.action, node=element)

__all__ = [
    "ApplyResult",
    "TranslationApplier",
]
