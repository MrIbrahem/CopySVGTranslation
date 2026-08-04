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
│   │   ├── README.md
│   │   └── strategies.py
│   ├── injection/
│   │   ├── __init__.py
│   │   ├── id_manager.py
│   │   ├── injector.py
│   │   ├── README.md
│   │   ├── switch_processor.py
│   │   └── translation_applier.py
│   ├── io/
│   │   ├── __init__.py
│   │   ├── mapping_store.py
│   │   ├── README.md
│   │   └── svg_document.py
│   ├── legacy/
│   │   ├── __init__.py
│   │   ├── extract.py
│   │   ├── inject.py
│   │   └── README.md
│   ├── nested/
│   │   ├── __init__.py
│   │   ├── detector.py
│   │   ├── flattener.py
│   │   └── README.md
│   ├── preparation/
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
│   │   ├── preparer.py
│   │   └── README.md
│   ├── titles/
│   │   ├── __init__.py
│   │   ├── README.md
│   │   └── year_handler.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── README.md
│   │   ├── text.py
│   │   └── xml.py
│   ├── __init__.py
│   ├── config.py
│   ├── exceptions.py
│   ├── README.md
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
├── tests/
│   ├── README.md
│   └── test_svg_extractor_class.py
├── _pyproject.toml
├── tree.md
└── v2.1_review.md

```