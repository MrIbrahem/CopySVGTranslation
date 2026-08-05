**Composite Matching Strategy — Details**

### Role

`CompositeMatchingStrategy` is the default way the extractor links **fallback (default) text segments** to **translated segments** inside the same `<switch>`.

It does not implement matching itself. It runs a list of strategies in order and returns the **first non-empty** result.

```text
ByTspanIdStrategy  →  if matches: use them
        ↓ empty
ByPositionStrategy →  if matches: use them
        ↓ empty
[] (no matches)
```

---

### Implementation (v2.1)

```python
class CompositeMatchingStrategy(MatchingStrategy):
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
```

Default pipeline: **ID-based first, position-based fallback.**

---

### Child strategies

#### 1. `ByTspanIdStrategy` (preferred)

**Idea:** Translated tspan ids are derived from default ids:

| Default id | Translated id examples     |
| ---------- | -------------------------- |
| `trsvg12`  | `trsvg12-ar`, `trsvg12_ar` |
| `foo`      | `foo-es`, `foo_es`         |

**Algorithm:**

1. For each default `<tspan>` with id + non-empty text:
    - `base = id.split("-")[0].split("_")[0]`
    - Map `base` → normalized default text (also `base.lower()`)
2. For each translated `<tspan>` with id + text:
    - Same `base` extraction
    - Lookup default text; if found → `SegmentMatch`

**Pros:** Correct when segment order differs or counts differ.
**Cons:** Fails if ids missing, unrelated, or base-splitting is wrong (`a-b-c` → base `a`).

**Note:** Only tspans with **both** id and text participate. Nodes with only element text (no tspans) yield no id matches → composite falls through to position.

---

#### 2. `ByPositionStrategy` (fallback)

**Idea:** Match by index:

```text
default.texts()[i]  ↔  translated.texts()[i]
```

Uses `TextNode.texts()` (tspans if present, else node text).

**Pros:** Works without ids; simple.
**Cons:** Wrong if order differs or one side has more/fewer segments; silently truncates to `min(len(default), len(translated))`.

---

### `SegmentMatch` payload

```python
@dataclass(slots=True)
class SegmentMatch:
    default_text: str      # key side (possibly lowercased)
    translated_text: str   # value side (normalized, not forced lower)
    default_id: str | None = None
    translated_id: str | None = None
```

Extractor then:

```python
key = normalize_text(m.default_text, case_insensitive)  # often already normalized
mapping.add(key, lang, m.translated_text, case_insensitive=False)
```

---

### How the extractor uses it

Per language node inside a switch:

```text
default = switch.fallback()
for node in switch.text_nodes():
    if node.is_fallback: continue
    matches = strategy.match(default, node, case_insensitive=...)
    for m in matches:
        mapping.add(...)
```

Composite is constructed in `SVGTranslationExtractor.__init__` if no strategy is injected:

```python
self.strategy = matching_strategy or CompositeMatchingStrategy()
```

---

### Behaviour matrix

| Situation                        | ByTspanId                  | ByPosition                       | Composite result                                |
| -------------------------------- | -------------------------- | -------------------------------- | ----------------------------------------------- |
| Good parallel ids                | Matches                    | (not tried)                      | ID matches                                      |
| Ids missing                      | `[]`                       | Index matches                    | Position matches                                |
| Ids present but unrelated        | `[]` or partial            | Index matches if id returns `[]` | Position only if id returned **empty**          |
| Partial id matches (some tspans) | **Non-empty partial list** | Not tried                        | **Partial ID matches only** — position not used |
| No tspans, plain text            | `[]`                       | Single segment match             | Position                                        |
| Empty translated text            | Skipped in both            | Skipped/empty                    | `[]`                                            |

**Important edge case:** If `ByTspanIdStrategy` returns a **partial** non-empty list (only some segments matched), composite **stops** and never runs position matching for the rest. That can drop translations.

---

### Design implications / gaps

1. **Partial ID matches block position fallback**

    - Current rule: `if result: return result`
    - Safer variants:
        - Require full coverage (`len(matches) == len(default_texts)`) before accepting ID strategy
        - Or merge: id matches first, fill holes by position

2. **Base-id parsing is naive**

    - `split("-")[0].split("_")[0]` breaks on ids that legitimately contain hyphens
    - v1 used similar logic; known limitation

3. **Case handling**

    - Default text normalized with `case_insensitive`
    - Translated text normalized without lowercasing
    - Consistent with mapping keys when extractor uses the same flags

4. **Extensibility**

    - Custom order: `CompositeMatchingStrategy([ByPositionStrategy(), ByTspanIdStrategy()])`
    - Custom strategies: implement `MatchingStrategy.match(...) -> list[SegmentMatch]`

5. **No config knob yet**
    - Strategy is constructor-injected, not on `TranslationConfig`
    - Optional future: `config.matching_strategy = "composite" | "id" | "position"`

---

### Suggested hardening (optional)

```python
def match(...):
    default_count = len(default_node.texts(normalize=True, case_insensitive=case_insensitive))
    for strategy in self.strategies:
        result = strategy.match(...)
        # Accept ID strategy only if it covers all default segments
        if result and (
            not isinstance(strategy, ByTspanIdStrategy)
            or len(result) >= default_count
        ):
            return result
    return []
```

Or explicit merge strategy instead of pure first-wins.

---

### Summary

| Item            | Detail                                                |
| --------------- | ----------------------------------------------------- |
| Default stack   | ByTspanId → ByPosition                                |
| Win rule        | First strategy that returns a non-empty list          |
| Risk            | Partial ID matches skip position fallback             |
| Injection point | `SVGTranslationExtractor(..., matching_strategy=...)` |
| Output          | `list[SegmentMatch]` consumed by `_process_switch`    |

Composite is the right default for real SVGs (id-rich when available, positional otherwise), but the **partial-match short-circuit** is the main behavioural subtlety to be aware of when debugging missed translations.
