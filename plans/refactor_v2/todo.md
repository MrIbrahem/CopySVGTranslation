# What’s left to do

Here’s a concise status of the whole thread and a prioritized backlog.

---

## Already done (design only)

| Area | Status |
|------|--------|
| Full engineering review | Done |
| README draft | Done |
| Analysis: `_validate_switch_languages`, `WrapTspans`, `fixer`, header | Done |
| `preparation/steps` class drafts + plan | Done (not implemented) |
| `nested/` + `extraction/` plans | Done (not implemented) |
| Golden-fixture testing guide | Done (fixtures/tests not created) |

Nothing from the refactor has been **implemented** in the repo yet — only designs and plans.

---

## Left to do (by priority)

### 1. Immediate – implement the agreed refactors

**A. `preparation/steps`** (plan already written)
- [ ] Add `ValidateSwitchLanguages`
- [ ] Add `RemoveEmptyNodes`
- [ ] Slim `NormalizeTspans` (drop `WrapTspans`)
- [ ] Move ID cleaning into `AssignIds`
- [ ] Slim `SplitLanguages` (no heavy validation)
- [ ] Wire new step order in `preparer.py` + `__init__.py`

**B. Golden baseline (before/while coding)**
- [ ] Add `tests/fixtures/svg/…` samples
- [ ] Generate golden SVG/JSON from **current** main
- [ ] Add `test_preparation_golden.py` (and extract/nested as needed)
- [ ] Confirm all goldens pass on main

**C. `nested/`**
- [ ] Drop or demote `MatchFixNestedTags` (`fixer.py`)
- [ ] Public API = `NestedTspanDetector` + `NestedTspanFlattener` only
- [ ] Optional thin legacy/CLI helper

**D. `extraction/`**
- [ ] Add `SwitchTranslationCollector`
- [ ] Add `HeaderMappingExtractor` (`header.py`)
- [ ] Remove/rename `header_adder.py` if it exists
- [ ] Point `SVGTranslationExtractor` at the new helpers

---

### 2. High priority – from the original review (still open)

| Item | Why |
|------|-----|
| Harden XML parser (XXE: `resolve_entities=False`, `no_network=True`) | Security |
| Unify errors on `OperationResult` at the service boundary | API consistency |
| Finish/review truncated injection code (`switch_processor`, `translation_applier`) | Correctness risk |
| Make `IdManager` the single source of ID allocation | Avoid drift |
| Minimal unit tests beyond goldens (strategies, `YearTitleHandler`, `IdManager`) | Safety net |

---

### 3. Medium term

- [ ] Extract a pure injection pipeline (prepared tree + mapping → tree)
- [ ] `ErrorCode` enum instead of free-form strings
- [ ] Single structural pass in preparation (fewer full-tree XPath walks)
- [ ] Secondary index for case-insensitive `TranslationMapping.lookup`
- [ ] Deprecation path for legacy `extract` / `inject_file_tree`
- [ ] Short domain-model notes (IDs, nested strategies, year titles)

---

### 4. Longer term

- [ ] Remove legacy API in a major version
- [ ] Path sandboxing + size/nesting limits for untrusted SVGs
- [ ] Structured logging
- [ ] Optional performance pass on `deepcopy` during language split

---

## Suggested sequence (next actions)

```text
1. Create golden fixtures + tests on current main
2. Implement preparation/steps refactor (Phase 1–3 of that plan)
3. Re-run goldens (must stay green with no golden updates)
4. nested cleanup → extraction collector/header
5. Parser hardening + error-result unification
6. Injection module review + IdManager consolidation
7. Broader unit tests + docs/README final pass
```

---

## One-line summary

**Design for preparation / nested / extraction is done; implementation, golden fixtures, security hardening, error unification, and injection cleanup are still ahead.**

If you want to continue in-repo next, the highest leverage step is: **add fixtures + goldens on main, then land the `preparation/steps` refactor.**
