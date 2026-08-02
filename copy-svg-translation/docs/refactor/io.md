**IO Package Design**

```
io/
├── __init__.py
├── svg_document.py      # SvgDocument – load / save / root access
└── mapping_store.py     # MappingStore – load / merge / save JSON mappings
```

This layer is the **only** place that touches the filesystem.
Everything else (core, extraction, injection, service) works with in-memory objects.

---

### 1. `svg_document.py`

```python
# io/svg_document.py
from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

from ..config import TranslationConfig
from ..exceptions import SvgStructureExceptionError  # or a dedicated IO error

logger = logging.getLogger(__name__)

SVG_NS = "http://www.w3.org/2000/svg"
XMLNS_ATTR = "{http://www.w3.org/2000/xmlns/}xmlns"


class SvgDocument:
    """
    Thin I/O + document holder around an lxml ElementTree.

    Responsibilities:
    - Load an SVG from disk
    - Ensure a sane default namespace
    - Expose root / tree
    - Save back to disk
    """

    def __init__(
        self,
        tree: etree._ElementTree,
        path: Path | None = None,
        *,
        config: TranslationConfig | None = None,
    ) -> None:
        self.tree = tree
        self.path = path
        self.config = config or TranslationConfig()
        self.root = tree.getroot()
        if self.root is None:
            raise SvgStructureExceptionError("structure-error-no-doc-element")

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------
    @classmethod
    def load(
        cls,
        path: Path | str,
        *,
        config: TranslationConfig | None = None,
    ) -> SvgDocument:
        path = Path(path)
        config = config or TranslationConfig()

        if not path.exists():
            raise FileNotFoundError(f"SVG file not found: {path}")

        parser = etree.XMLParser(remove_blank_text=config.remove_blank_text)

        try:
            tree = etree.parse(str(path), parser)
        except (etree.XMLSyntaxError, OSError) as exc:
            logger.error("Failed to parse SVG %s: %s", path, exc)
            raise

        doc = cls(tree, path=path, config=config)
        doc._ensure_namespace()
        return doc

    # ------------------------------------------------------------------
    # Namespace helper
    # ------------------------------------------------------------------
    def _ensure_namespace(self) -> None:
        """Guarantee the document has a proper default SVG namespace."""
        import re

        default_ns = self.root.nsmap.get(None)
        if default_ns is None or re.match(r"^(&[^;]+;)+$", str(default_ns)):
            self.root.set(XMLNS_ATTR, SVG_NS)

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def save(
        self,
        path: Path | str | None = None,
        *,
        pretty_print: bool | None = None,
        create_parents: bool | None = None,
    ) -> Path:
        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("No target path provided for save")

        cfg = self.config
        pretty = cfg.pretty_print if pretty_print is None else pretty_print
        create = cfg.create_parents if create_parents is None else create_parents

        if create:
            target.parent.mkdir(parents=True, exist_ok=True)

        self.tree.write(
            str(target),
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=pretty,
        )
        logger.debug("Saved SVG to %s", target)
        return target

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def xpath(self, expression: str, namespaces: dict | None = None):
        ns = namespaces or {"svg": SVG_NS}
        return self.root.xpath(expression, namespaces=ns)

    def findall(self, tag: str):
        """Find all elements with the given local tag name in the SVG namespace."""
        return self.root.findall(f".//{{{SVG_NS}}}{tag}")
```

---

### 2. `mapping_store.py`

```python
# io/mapping_store.py
from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from pathlib import Path

from ..config import TranslationConfig
from ..core.mapping import TranslationMapping

logger = logging.getLogger(__name__)


class MappingStore:
    """
    Load, merge and save translation mappings as JSON.
    """

    def __init__(self, config: TranslationConfig | None = None) -> None:
        self.config = config or TranslationConfig()

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------
    def load(self, path: Path | str) -> TranslationMapping:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Mapping file not found: {path}")

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        mapping = TranslationMapping.from_any(data)
        logger.debug("Loaded mapping from %s (%d entries)", path, len(mapping.new))
        return mapping

    def load_many(self, paths: Iterable[Path | str]) -> TranslationMapping:
        """Load and merge multiple mapping files."""
        result = TranslationMapping()
        for p in paths:
            try:
                result.merge(self.load(p))
            except FileNotFoundError:
                logger.warning("Mapping file not found, skipped: %s", p)
            except Exception as exc:
                logger.error("Failed to load mapping %s: %s", p, exc)
        return result

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def save(
        self,
        mapping: TranslationMapping,
        path: Path | str,
        *,
        create_parents: bool | None = None,
        indent: int = 2,
    ) -> Path:
        path = Path(path)
        create = (
            self.config.create_parents
            if create_parents is None
            else create_parents
        )

        if create:
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                mapping.to_dict(),
                f,
                indent=indent,
                ensure_ascii=False,
            )

        logger.debug("Saved mapping to %s", path)
        return path

    # ------------------------------------------------------------------
    # Helpers used by the service
    # ------------------------------------------------------------------
    def default_mapping_path(self, svg_path: Path) -> Path:
        """Return the conventional path for a mapping extracted from an SVG."""
        base_dir = self.config.mapping_output_dir or Path.cwd() / "data"
        return base_dir / f"{svg_path.name}.json"
```

---

### 3. `io/__init__.py`

```python
from .svg_document import SvgDocument
from .mapping_store import MappingStore

__all__ = [
    "SvgDocument",
    "MappingStore",
]
```

---

### How the rest of the system uses IO

| Caller                                           | Usage                                                                                                       |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| **SvgPreparationPipeline** (`LoadDocument` step) | `SvgDocument.load(path)` → puts `tree` / `root` into `PreparationContext`                                   |
| **SVGTranslationInjector**                       | Receives an already-loaded tree (or loads via `SvgDocument` if needed); calls `doc.save()` when `save=True` |
| **SVGTranslationService**                        | Uses `MappingStore` for `load_mapping` / `save_mapping` and for optional auto-save of extracted mappings    |
| **Legacy workflows**                             | Can be re-implemented as thin wrappers around `MappingStore` + `SvgDocument`                                |

---

### Design principles

1. **Single responsibility** — IO package only reads/writes disk and holds the raw document.
2. **Config-driven** — `pretty_print`, `create_parents`, `remove_blank_text`, default directories all come from `TranslationConfig`.
3. **No domain logic** — Does not interpret switches, languages, or translations.
4. **Clean errors** — File-not-found and parse errors surface as normal exceptions; the service turns them into `OperationResult.fail(...)`.
5. **Easy to mock** — In tests you can build an `SvgDocument` from an in-memory tree without touching disk.

---

### Typical flow

```
Service.extract(path)
    → MappingStore not used yet
    → Extractor works on SvgDocument.load(path).root
    → optional MappingStore.save(mapping, ...)

Service.inject(path, mapping, output=..., save=True)
    → SvgDocument.load(path)          # or already prepared tree
    → ... injection ...
    → doc.save(output)
```

This keeps all filesystem concerns isolated and makes the rest of the redesign easier to test and reason about.
