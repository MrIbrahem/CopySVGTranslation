# Getting Started

> **Relevant source files**
> * [.github/workflows/python-publish.yml](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/.github/workflows/python-publish.yml)
> * [CLAUDE.md](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/CLAUDE.md?plain=1)
> * [README.md](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/README.md?plain=1)
> * [pyproject.toml](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/pyproject.toml)
> * [requirements.txt](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/requirements.txt)

This page provides an introduction to installing and using CopySVGTranslation. It covers system requirements, the basic translation workflow, and the primary functions you will use to extract and inject translations. For detailed installation instructions, see [Installation](/MrIbrahem/CopySVGTranslation/2.1-installation). For a hands-on tutorial with complete examples, see [Quick Start Tutorial](/MrIbrahem/CopySVGTranslation/2.2-quick-start-tutorial).

## Purpose and Scope

CopySVGTranslation is a Python package for managing multilingual SVG files. It enables you to:

* Extract translations from SVG files that already contain multiple languages within `<switch>` elements.
* Store translations in a structured JSON format (`TranslationMapping`).
* Apply translations to other SVG files by inserting or updating `<text systemLanguage="XX">` elements.
* Repair complex SVG structures like nested `<tspan>` or `<a>` tags.

The package provides a high-level facade, `SVGTranslationService`, to coordinate these operations through a unified interface.

**Sources:** [README.md L1-L20](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/README.md?plain=1#L1-L20)

 [CLAUDE.md L7-L8](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/CLAUDE.md?plain=1#L7-L8)

## Prerequisites

Before installing CopySVGTranslation, ensure your environment meets these requirements:

| Requirement | Version | Purpose |
| --- | --- | --- |
| Python | 3.11+ | Core language runtime |
| lxml | 4.9+ | XML/SVG parsing and manipulation |

The library is designed for modern Python environments and relies heavily on `lxml` for robust XML processing.

**Sources:** [pyproject.toml L10-L13](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/pyproject.toml#L10-L13)

 [requirements.txt L1](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/requirements.txt#L1-L1)

## Installation Overview

Install CopySVGTranslation from PyPI using pip:

```
pip install CopySVGTranslation
```

This installs the package and its core dependency (`lxml`). For complete installation details including virtual environment setup and development dependencies, see [Installation](/MrIbrahem/CopySVGTranslation/2.1-installation).

After installation, the primary way to interact with the library is through the `SVGTranslationService`:

```javascript
from CopySVGTranslation import SVGTranslationService, TranslationConfig
```

**Sources:** [README.md L24-L30](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/README.md?plain=1#L24-L30)

 [README.md L41-L43](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/README.md?plain=1#L41-L43)

## Understanding the Translation Workflow

CopySVGTranslation uses a modular pipeline for managing translations, coordinated by the service facade.

### Workflow Diagram

```

```

**Sources:** [CLAUDE.md L57-L61](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/CLAUDE.md?plain=1#L57-L61)

 [README.md L82-L92](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/README.md?plain=1#L82-L92)

### Phase Descriptions

**Phase 1: Extraction** ([Extraction](/MrIbrahem/CopySVGTranslation/4.1-extraction)) reads a source SVG file. The internal `SVGTranslationExtractor` parses `<switch>` elements to identify existing translations. It produces a `TranslationMapping` object containing text pairs and metadata.

**Phase 2: Storage** persists the `TranslationMapping` to a JSON file. This allows for manual review or version control of translations outside of the SVG XML structure.

**Phase 3: Injection** ([Injection](/MrIbrahem/CopySVGTranslation/4.2-injection)) applies a `TranslationMapping` to a target SVG. The internal `SVGTranslationInjector` prepares the SVG (normalizing IDs and tags) and delegates to the `switch_processor` to insert or update `systemLanguage` blocks.

For a detailed explanation of each phase, see [SVG Translation Workflow](/MrIbrahem/CopySVGTranslation/3.1-svg-translation-workflow).

**Sources:** [CLAUDE.md L31-L56](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/CLAUDE.md?plain=1#L31-L56)

 [README.md L123-L136](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/README.md?plain=1#L123-L136)

## Core Entities and Data Flow

The following diagram maps the high-level Service Facade to the internal implementation modules:

```

```

### Key Classes

| Class | Purpose | Module |
| --- | --- | --- |
| `SVGTranslationService` | The high-level facade for all operations | `CopySVGTranslation.service` |
| `TranslationConfig` | Configuration for matching, directories, and overwriting | `CopySVGTranslation.config` |
| `TranslationMapping` | The standard data model for SVG translations | `CopySVGTranslation.models` |
| `OperationResult` | Uniform return type containing success status, data, and stats | `CopySVGTranslation.models` |

**Sources:** [CLAUDE.md L33-L56](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/CLAUDE.md?plain=1#L33-L56)

 [README.md L72-L81](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/README.md?plain=1#L72-L81)

 [README.md L97-L120](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/README.md?plain=1#L97-L120)

## Translation Data Format

The JSON structure produced by the service uses a nested format to organize translations by source text and language code.

```json
{  "new": {    "Source English Text": {      "ar": "النص المترجم للعربية",      "fr": "Texte traduit en français"    }  },  "tspans_by_id": {},  "title_new": {},  "meta": {}}
```

The `"new"` key acts as the primary namespace where the key is the normalized source text and the value is a dictionary of language codes to their respective translations.

**Sources:** [CLAUDE.md L64-L73](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/CLAUDE.md?plain=1#L64-L73)

 [README.md L149-L171](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/README.md?plain=1#L149-L171)

## Basic Usage Pattern

The most common workflow is the combined "extract and inject" operation, which takes translations from one file and applies them to another in a single step.

```javascript
from CopySVGTranslation import SVGTranslationService, TranslationConfig # 1. Setup Configurationconfig = TranslationConfig(    overwrite_translations=True,    pretty_print=True) # 2. Initialize Serviceservice = SVGTranslationService(config) # 3. Execute Workflowresult = service.extract_and_inject(    source="multilingual_source.svg",    output="target_to_translate.svg",    save=True) # 4. Handle Resultif result.success:    print(f"Inserted: {result.stats.inserted_translations}")else:    print(f"Error: {result.error}")
```

**Sources:** [README.md L34-L66](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/README.md?plain=1#L34-L66)

 [README.md L88](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/README.md?plain=1#L88-L88)

## Next Steps

Now that you understand the basic workflow and primary functions, you can:

1. **Follow the hands-on tutorial**: See [Quick Start Tutorial](/MrIbrahem/CopySVGTranslation/2.2-quick-start-tutorial) for a complete walkthrough.
2. **Learn about text normalization**: See [Text Normalization](/MrIbrahem/CopySVGTranslation/3.4-text-normalization) to understand how the system matches text across files.
3. **Explore result handling**: See [Handle Results Consistently](#97) in the README for details on the `OperationResult` object.
4. **Review the complete API**: See [API Reference](/MrIbrahem/CopySVGTranslation/6-api-reference) for detailed documentation of all service methods.
5. **Handle advanced scenarios**: See [Advanced Features](/MrIbrahem/CopySVGTranslation/5-advanced-features) for year-based title handling and SVG preparation pipelines.

**Sources:** General guidance based on table of contents structure.