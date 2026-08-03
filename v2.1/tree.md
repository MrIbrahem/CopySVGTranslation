```
v2.1/
├── copy_svg_translation/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── mapping.py
│   │   ├── models.py
│   │   ├── README.md
│   │   ├── switch_node.py
│   │   └── text_node.py
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── extractor.py
│   │   └── strategies.py
│   ├── injection/
│   │   ├── steps/
│   │   │   ├── __init__.py
│   │   │   ├── assign_ids.py
│   │   │   ├── base.py
│   │   │   ├── load.py
│   │   │   ├── normalize_tspans.py
│   │   │   ├── reorder.py
│   │   │   ├── split_languages.py
│   │   │   └── validate.py
│   │   ├── __init__.py
│   │   ├── id_manager.py
│   │   ├── injector.py
│   │   ├── preparer.py
│   │   ├── switch_processor.py
│   │   └── translation_applier.py
│   ├── io/
│   │   ├── __init__.py
│   │   ├── mapping_store.py
│   │   └── svg_document.py
│   ├── legacy/
│   │   ├── __init__.py
│   │   ├── extract.py
│   │   ├── inject.py
│   ├── nested/
│   │   ├── __init__.py
│   │   ├── detector.py
│   │   └── flattener.py
│   ├── titles/
│   │   ├── __init__.py
│   │   └── year_handler.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── text.py
│   │   └── xml.py
│   ├── __init__.py
│   ├── config.py
│   ├── exceptions.py
│   ├── result.py
│   └── service.py
├── docs/
│   └── refactor/
│       ├── core.md
│       ├── exceptions.md
│       ├── extraction.md
│       ├── init.md
│       ├── injection.md
│       ├── io.md
│       ├── legacy.md
│       ├── nested.md
│       ├── preparation.md
│       ├── pyproject.toml.md
│       ├── README.md
│       ├── titles.md
│       └── utils.md

```
