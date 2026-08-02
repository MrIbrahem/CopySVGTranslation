# service.py
from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from lxml import etree

from .config import TranslationConfig
from .core.mapping import TranslationMapping
from .result import InjectResult, OperationResult

logger = logging.getLogger(__name__)


class SVGTranslationService:
    """
    Main public facade for SVG translation extraction and injection.
    """

    def __init__(self, config: TranslationConfig | None = None) -> None:
        self.config = config or TranslationConfig()
        self._extractor = None
        self._injector = None
        self._mapping_store = None

    def extract(
        self,
        svg_path: Path | str,
        *,
        save_mapping: bool | Path | None = None,
    ) -> OperationResult[TranslationMapping]:
        """
        Extract translations from an SVG file.
        """
        svg_path = Path(svg_path)

        try:
            mapping = self._get_extractor().extract(svg_path)
        except Exception as exc:
            logger.exception("Extraction failed for %s", svg_path)
            return OperationResult.fail(
                error=str(exc),
                error_code=getattr(exc, "code", "extraction_error"),
            )

        if not mapping or mapping.is_empty():
            return OperationResult.fail(
                error="No translations found or file could not be parsed",
                error_code="no_translations",
            )

        warnings: list[str] = []

        if save_mapping:
            try:
                out = self._resolve_mapping_output(svg_path, save_mapping)
                self._get_mapping_store().save(mapping, out)
            except (OSError, Exception) as exc:
                warnings.append(f"Failed to save mapping: {exc}")

        return OperationResult.ok(data=mapping, warnings=warnings)

    def inject(
        self,
        svg_path: Path | str,
        mapping: TranslationMapping | Mapping[str, Any],
        *,
        output: Path | str | None = None,
        save: bool | None = None,
    ) -> InjectResult:
        """
        Inject translations into an SVG file.
        """
        svg_path = Path(svg_path)
        should_save = self.config.auto_save if save is None else save

        if should_save and output is None:
            return OperationResult.fail(
                error="save=True but no output path provided",
                error_code="missing_output_path",
            )

        try:
            normalized = TranslationMapping.from_any(mapping)
            resolved_output = self._resolve_output_path(output) if output else None
            tree, stats = self._get_injector().inject(
                svg_path,
                normalized,
                target_path=resolved_output,
                save=should_save,
            )
        except Exception as exc:
            logger.exception("Injection failed for %s", svg_path)
            return OperationResult.fail(
                error=str(exc),
                error_code=getattr(exc, "code", "injection_error"),
            )

        if tree is None:
            return OperationResult.fail(
                error="Injection returned no tree",
                error_code="injection_failed",
                stats=stats,
            )

        return OperationResult.ok(data=tree, stats=stats)

    def extract_and_inject(
        self,
        source: Path | str,
        target: Path | str,
        *,
        output: Path | str | None = None,
        save_mapping: bool | Path | None = None,
        save: bool | None = None,
    ) -> InjectResult:
        """
        Extract translations from `source` and inject them into `target`.
        """
        extract_result = self.extract(source, save_mapping=save_mapping)
        if not extract_result.success or extract_result.data is None:
            return OperationResult.fail(
                error=extract_result.error or "Extraction failed",
                error_code=extract_result.error_code,
                warnings=extract_result.warnings,
            )

        inject_result = self.inject(
            target,
            extract_result.data,
            output=output,
            save=save,
        )

        merged_warnings = extract_result.warnings + inject_result.warnings
        return OperationResult(
            success=inject_result.success,
            data=inject_result.data,
            stats=inject_result.stats,
            error=inject_result.error,
            error_code=inject_result.error_code,
            warnings=merged_warnings,
        )

    def prepare_only(
        self,
        svg_path: Path | str,
        *,
        output: Path | str | None = None,
    ) -> InjectResult:
        """
        Run only the preparation pipeline.
        """
        svg_path = Path(svg_path)

        try:
            tree = self._get_injector().prepare(svg_path)
            if output:
                resolved_output = self._resolve_output_path(output)
                self._save_tree(tree, resolved_output)
            return OperationResult.ok(data=tree)
        except Exception as exc:
            return OperationResult.fail(
                error=str(exc),
                error_code=getattr(exc, "code", "prepare_error"),
            )

    def load_mapping(self, path: Path | str) -> OperationResult[TranslationMapping]:
        """Load a previously saved JSON mapping file."""
        try:
            mapping = self._get_mapping_store().load(Path(path))
            return OperationResult.ok(data=mapping)
        except Exception as exc:
            return OperationResult.fail(error=str(exc), error_code="load_mapping_error")

    def save_mapping(
        self,
        mapping: TranslationMapping,
        path: Path | str,
    ) -> OperationResult[Path]:
        """Save a mapping to JSON."""
        path = Path(path)
        try:
            self._get_mapping_store().save(mapping, path)
            return OperationResult.ok(data=path)
        except Exception as exc:
            return OperationResult.fail(error=str(exc), error_code="save_mapping_error")

    def _get_extractor(self):
        if self._extractor is None:
            from .extraction.extractor import SVGTranslationExtractor

            self._extractor = SVGTranslationExtractor(self.config)
        return self._extractor

    def _get_injector(self):
        if self._injector is None:
            from .injection.injector import SVGTranslationInjector

            self._injector = SVGTranslationInjector(self.config)
        return self._injector

    def _get_mapping_store(self):
        if self._mapping_store is None:
            from .io.mapping_store import MappingStore

            self._mapping_store = MappingStore(self.config)
        return self._mapping_store

    def _resolve_output_path(self, output: Path | str) -> Path:
        output = Path(output)
        if output.parent == Path(".") and self.config.output_dir is not None:
            return self.config.output_dir / output
        return output

    def _resolve_mapping_output(
        self,
        svg_path: Path,
        save_mapping: bool | Path,
    ) -> Path:
        if isinstance(save_mapping, str | Path):
            return Path(save_mapping)

        if self.config.mapping_output_dir is None:
            raise ValueError("mapping_output_dir is not configured; cannot resolve mapping output path")

        base_dir = self.config.mapping_output_dir
        if self.config.create_parents:
            base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / f"{svg_path.name}.json"

    def _save_tree(self, tree: etree._ElementTree, path: Path) -> None:
        if self.config.create_parents:
            path.parent.mkdir(parents=True, exist_ok=True)
        tree.write(
            str(path),
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=self.config.pretty_print,
        )
