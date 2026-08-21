Old pattern — direct call to the internal inject_file_tree function:

```python
  tree, stats = inject_file_tree(
      inject_file=svg_path,
      mapping=mappings,
      case_insensitive=False,
      return_stats=True,
  )
```

New pattern — using the public SVGTranslationService facade:

```python
  service = SVGTranslationService(TranslationConfig(case_insensitive=False))

  result = service.inject(
      svg_path=svg_path,
      mapping=mappings,
      output=svg_path,
  )

  assert isinstance(result.data, InjectorData)
  tree = result.data.tree
  stats = result.data.inject_stats.to_json()
```

Key differences:

1.  Service instantiation — SVGTranslationService with a TranslationConfig replaces raw keyword args like
    case_insensitive
2.  Result access — Instead of a (tree, stats) tuple, results come via result.data (an InjectorData object)
3.  Stats format — Stats are accessed through result.data.inject_stats.to_json() instead of being returned directly
4.  Output path — The new API takes an explicit output parameter

----------------------
Key challenge: The legacy inject_file_tree accepts mapping_files (list of file paths to JSON mappings), but the new
SVGTranslationService.inject() only accepts mapping (a dict or TranslationMapping). When tests use mapping_files, I
need to convert that to loading the mapping first using MappingStore.load_many() or service.load_mapping().

Let me categorize each test file and its inject_file_tree calls:

### 1. tests/e2e/extraction/test_extract.py

-   test_inject_with_return_stats: inject_file_tree(mapping=..., inject_file=..., return_stats=True) → simple
-   test_inject_with_overwrite: inject_file_tree(mapping=..., inject_file=..., overwrite_translations=True,
    return_stats=True) → simple

### 2. tests/e2e/injection/test_inject2.py

-   test_adds_text_to_switch: inject_file_tree(inject_file=..., save_path=..., mapping=..., overwrite_translations=True,
    pretty_print=True) → needs save_path → output with save=True
-   test_inject: inject_file_tree(inject_file=..., save_path=..., mapping=..., pretty_print=False, sort_switches=True) →
    similar

### 3. tests/e2e/injection/test_inject_extended.py

-   test_inject_with_invalid_svg_structure: inject_file_tree(inject_file=..., mapping=..., return_stats=True) → simple
-   test_inject_case_insensitive_false: inject_file_tree(inject_file=..., mapping=..., case_insensitive=False) → simple,
    no return_stats
-   test_inject_save_result_creates_output_file: inject_file_tree(inject_file=..., mapping=..., save_path=...) → needs
    output + save=True

### 4. tests/e2e/injection/test_language_tracking.py

-   test_inject_tracks_new_languages: inject_file_tree(inject_file=..., mapping=..., save_result=False,
    return_stats=True) → simple
-   test_inject_tracks_only_truly_new_languages: similar
-   test_file_langs_handles_element_tree: similar

### 5. tests/e2e/legacy/test_additional.py

-   test_inject_basic_workflow: inject_file_tree(mapping=..., inject_file=..., return_stats=True, save_result=True) → no
    save_path so save_result=True but no output. Actually wait, looking more carefully, the legacy function has
    save_result=False and the test passes save_result=True. The legacy function has save_result or bool(save_path)
    logic. In the new API, if save=True but no output, the service returns a fail result. Let me look at this more
    carefully.

Actually wait, let me re-read the legacy function:

```python
  def inject_file_tree(..., save_result=False, ...):
      tree, stats = _inject_file_tree(
          ...
          save_result=save_result or bool(save_path),
          ...
      )
```

And \_inject_file_tree calls:

```python
  config = TranslationConfig(..., auto_save=False)
  service = SVGTranslationService(config)
  result = service.inject(svg_path=inject_path, mapping=mapping_obj, output=save_path, save=save_result)
```

So save_result=True with no save_path → service.inject(output=None, save=True) → but the service says:

```python
  if should_save and output is None:
      return OperationResult.fail(...)
```

Hmm, but the test asserts tree is None for test_inject_basic_workflow. Let me look at the legacy again:

```python
  if not result.success or result.data is None:
      return (None, {"error": "error"})
```

So when save_result=True but no save_path, the service fails, and the legacy returns (None, {"error": "error"}).
That's why tree is None in the test.

So for this test, the behavior is: inject with save=True but no output → fail → tree is None. The new API does the
same thing. Let me think about how to translate this.

Actually, the test is:

```python
  tree, stats = inject_file_tree(mapping=..., inject_file=target, return_stats=True, save_result=True)
  assert tree is None
```

With the new API:

```python
  service = SVGTranslationService(TranslationConfig())
  result = service.inject(svg_path=target, mapping=..., save=True)  # no output
  # result.success should be False
  assert result.data is None or not result.success
```

Actually, this test is checking that when save_result=True but no save_path, the operation fails. So the new API
should handle this the same way. Let me write it properly.

Wait, looking at test_inject_basic_workflow again:

```python
  def test_inject_basic_workflow(self, temp_dir):
      """Test basic inject workflow."""
      target = temp_dir / "target.svg"
      content = """..."""
      target.write_text(content, encoding="utf-8")
      translations = {"new": {"hi": {"ar": "مرحبا"}}}
      tree, stats = inject_file_tree(
          mapping=translations,
          inject_file=target,
          return_stats=True,
          save_result=True,
      )
      assert tree is None
```

Hmm, the test expects tree to be None. That's testing a error case (save without output path). With the new API:

```python
  service = SVGTranslationService()
  result = service.inject(svg_path=target, mapping=translations, save=True)
  assert not result.success
```

### 6. tests/e2e/legacy/test_comprehensive.py

-   test_inject_with_all_mappings_parameter: inject_file_tree(inject_file=..., mapping=..., return_stats=True) → simple
-   test_inject_with_save_path: inject_file_tree(inject_file=..., mapping=..., save_path=...) → output + save=True
-   test_inject_case_sensitive: ALREADY MIGRATED to new API! Only first two tests need updating.

### 7. tests/e2e/legacy/test_full.py

Many calls:

-   test_inject_uses_existing_mapping: uses extract() result as mapping, save_path=..., return_stats=True
-   test_inject_without_save_path: save_result=False, return_stats=True
-   test_inject_returns_stats: return_stats=True
-   test_inject_without_stats: return_stats=False
-   test_inject_with_empty_translations: return_stats=True
-   test_inject_multiple_operations: save_path=..., return_stats=True (two calls)

### 8. tests/e2e/svg_translate/test_svgtranslate.py

Uses mapping_files parameter in many tests:

-   test_inject: inject_file_tree(inject_file=..., mapping_files=[...], return_stats=True, save_path=...,
    save_result=True)
-   test_inject_dry_run: inject_file_tree(inject_file=..., mapping_files=[...], return_stats=True)
-   test_inject_overwrite: inject_file_tree(inject_file=..., mapping_files=[...], overwrite_translations=True,
    return_stats=True, save_path=..., save_result=True)
-   test_inject_nonexistent_file: inject_file_tree(inject_file=..., mapping_files=[...])
-   test_inject_nonexistent_mapping: inject_file_tree(inject_file=..., mapping_files=[...])

### 9. tests/e2e/svg_translate/test_svgtranslate_extended.py

More mapping_files usage:

-   test_inject_with_multiple_mapping_files: mapping_files=[path1, path2]
-   test_inject_with_output_directory: mapping_files=[path], save_path=..., save_result=True
-   test_inject_preserves_original_structure: mapping_files=[path]
-   test_inject_without_overwrite_skips_existing: mapping_files=[path], overwrite_translations=False, return_stats=True,
    save_path=..., save_result=True
-   test_inject_stats_accuracy: mapping_files=[path], overwrite_translations=True, return_stats=True
-   test_extract_and_inject_roundtrip: mapping_files=[path], return_stats=True
-   test_inject_empty_mapping_file: mapping_files=[path], return_stats=True
-   test_inject_invalid_json_mapping: mapping_files=[path]

### 10. tests/e2e/test_manual_workflows.py

-   test_inject_after_normalization: inject_file_tree(inject_file=..., save_path=..., mapping=...,
    overwrite_translations=True, pretty_print=False, save_result=True)

### 11. tests/e2e/test_public_api.py

-   test_inject_with_dict: inject_file_tree(inject_file=..., mapping=..., save_path=..., return_stats=True,
    save_result=True)
-   test_inject_with_empty_mapping_list_raises: inject_file_tree(inject_file=..., mapping_files=[]) → expects TypeError

### 12. tests/unit/injection/test_worker.py

Just imports inject_file_tree - no actual tests using it. Just the import.

### 13. tests/unit/legacy/test_injection_worker.py

Just imports inject_file_tree - no actual tests using it. Just the import and a comment "TODO: write tests".

### 14. tests/unit/test_examples.py

-   test_inject_with_dict: inject_file_tree(inject_file=..., save_path=..., mapping=..., return_stats=True,
    save_result=True)

Now let me create a plan. The main patterns to convert:

Pattern A: Simple inject with mapping= dict and return_stats=True

```python
  # Old
  tree, stats = inject_file_tree(inject_file=svg_path, mapping=mappings, return_stats=True)
  # New
  service = SVGTranslationService()
  result = service.inject(svg_path=svg_path, mapping=mappings, output=svg_path)
  assert result.success
  tree = result.data.tree
  stats = result.data.inject_stats.to_json()
```

Pattern B: Inject with case_insensitive=False

```python
  service = SVGTranslationService(TranslationConfig(case_insensitive=False))
```

Pattern C: Inject with save_path=...

```python
  result = service.inject(svg_path=..., mapping=..., output=save_path, save=True)
```

Pattern D: Inject with overwrite_translations=True

```python
  service = SVGTranslationService(TranslationConfig(overwrite_translations=True))
```

Pattern E: Inject with pretty_print=True/False

```python
  service = SVGTranslationService(TranslationConfig(pretty_print=True))
```

Pattern F: Inject with sort_switches=True

```python
  service = SVGTranslationService(TranslationConfig(sort_switches=True))
```

Pattern G: Inject with mapping_files=[...]
Need to load mappings first:

```python
  from CopySVGTranslation.io.mapping_store import MappingStore
  store = MappingStore()
  mapping = store.load_many([path1, path2])
  # or for single file:
  mapping = store.load(path)
```

Pattern H: No return_stats (just tree)

```python
  result = service.inject(svg_path=..., mapping=..., output=...)
  tree = result.data.tree if result.success else None
```

Pattern I: save_result=False (no save, no output)

```python
  result = service.inject(svg_path=..., mapping=..., save=False)
```

Wait, there's a subtlety. When save=False and no output, the service still works. Let me check:

```python
  if should_save and output is None:
      return OperationResult.fail(...)
```

So if save=False, it doesn't need output. Good.

But actually, looking more carefully at service.inject():

```python
  def inject(self, svg_path, mapping, *, output=None, save=None):
      should_save = self.config.auto_save if save is None else save
      if should_save and output is None:
          return OperationResult.fail(...)
      ...
      resolved_output = self._resolve_output_path(output) if output else None
      injector_data = self._injector.inject(svg_path, normalized, save_path=resolved_output, save=should_save)
```

So save=False, output=None → works fine, no saving.
And save=True, output=some_path → saves to path.
And save=False, output=some_path → doesn't save (but output is ignored effectively).

Actually wait, the \_injector.inject still gets save_path=resolved_output. Let me check if the injector uses save_path
even when save=False... Let me check the injector.

Actually, looking at the legacy function \_inject_file_tree:

```python
  config = TranslationConfig(..., auto_save=False)
  service = SVGTranslationService(config)
  result = service.inject(svg_path=inject_path, mapping=mapping_obj, output=save_path, save=save_result)
```

The config has auto_save=False, so the default is no-save. And then save=save_result overrides it.

OK so in the new tests, when I use save=True I need output, and when I don't want to save, I use save=False (or just
don't pass it, relying on config's auto_save=False which is the default).

Now, there's one important thing: when tests use save_path=file and save_result=True, the legacy function would write
to that file. With the new API, I pass output=file, save=True.

But what about when a test only has save_path=... but NOT save_result=True? Let me check the legacy:

```python
  save_result=save_result or bool(save_path)
```

So if save_path is set, save_result becomes True automatically. So any call with save_path=X implies save=True.

Now let me also think about the mapping_files conversion. The legacy function handled loading JSON mapping files
internally. The new API doesn't have that. For tests using mapping_files, I need to either:

1.  Load the mapping first with MappingStore
2.  Use service.load_mapping() for single files

For consistency with the plan, I'll use MappingStore to load mappings before calling service.inject().

Let me also think about the test_inject_with_empty_mapping_list_raises test in test_public_api.py:

```python
  with pytest.raises(TypeError) as excinfo:
      result = inject_file_tree(inject_file=target_svg, mapping_files=[])
```

This expects a TypeError. With the legacy code, mapping_files=[] means not mapping and mapping_files is True (empty
list is falsy), so it falls through to the service with mapping=None. Then TranslationMapping.from_any(None) would
raise a TypeError. With the new API, we'd need to test this differently. Actually, looking at the legacy
\_inject_file_tree:

```python
  if not mapping and mapping_files:
      ...load mappings...
```

If mapping_files=[], this condition is False (empty list is falsy). So mapping stays None. Then later
TranslationMapping.from_any(None) raises TypeError because None is not a dict/Mapping/TranslationMapping.

For the new API, we'd pass mapping=None to service.inject() which calls TranslationMapping.from_any(None) → TypeError.
Or we could use service.inject(mapping={}) which would work but not raise.

Actually, let me think about this differently. The test is checking edge case behavior. With the new API, passing None
as mapping would still raise TypeError:

```python
  service = SVGTranslationService()
  with pytest.raises(TypeError):
      service.inject(svg_path=target_svg, mapping=None)
```

But wait, service.inject has mapping: TranslationMapping | Mapping[str, Any] type hint. If we pass None, it should
still raise. Let me check: TranslationMapping.from_any(None) → the function checks if isinstance(data,
TranslationMapping): return data → then checks if not isinstance(data_json, dict) and not isinstance(data_json,
Mapping): raise TypeError(...). So None would raise TypeError. Good.

Now let me also think about the test_inject_nonexistent_file and test_inject_nonexistent_mapping tests.

test_inject_nonexistent_file:

```python
  result = inject_file_tree(inject_file=nonexistent_path, mapping_files=[mapping_path])
  assert result is None
```

With new API: service.inject(svg_path=nonexistent_path, mapping=...) → should fail (file not found). The service
catches the exception and returns OperationResult.fail(...). So result.success == False.

test_inject_nonexistent_mapping:

```python
  result = inject_file_tree(inject_file=svg_path, mapping_files=[nonexistent_mapping])
```

With the legacy, MappingStore.load_many would skip the nonexistent file, resulting in an empty mapping, then
\_inject_file_tree returns (None, {"error": "No valid mappings found"}).
With new API, we need to load the mapping ourselves, and handle the FileNotFoundError. Or use MappingStore.load_many
which catches and skips missing files, resulting in an empty mapping. Then service.inject() with empty mapping...

Actually, let me think about this. MappingStore.load_many with a nonexistent file logs a warning and returns an empty
TranslationMapping(). Then when we call service.inject() with that empty mapping, it would succeed (the service
handles empty mappings fine - it just does nothing). That's different from the legacy behavior which returns (None,
{"error": ...}).

Hmm, but actually looking more carefully at \_inject_file_tree:

```python
  if not mapping and mapping_files:
      store = MappingStore()
      mapping_obj = store.load_many(mapping_files)
      if mapping_obj.is_empty():
          return (None, {"error": "No valid mappings found"})
      mapping = mapping_obj.to_json()
```

So it checks mapping_obj.is_empty() and returns early with error. The new service doesn't do this check - it just
injects with whatever mapping is given (even empty).

For the test migration, I need to replicate the behavior. Let me think...

For tests that specifically test the legacy behavior of "empty mapping → error", I should:

1.  Load the mapping with MappingStore
2.  Check if it's empty
3.  If empty, assert that (the test expectation)

Or better: since we're migrating to the new API, the behavior changes. The new API accepts empty mappings. So I should
adjust the test to match new behavior, OR I should note that the behavior changed.

Actually, let me re-read the plan:

```
  old:
  tree, stats = inject_file_tree(...)

  new:
  service = SVGTranslationService(TranslationConfig(...))
  result = service.inject(svg_path=..., mapping=..., output=...)
  assert isinstance(result.data, InjectorData)
  tree = result.data.tree
  stats = result.data.inject_stats.to_json()
```

The plan says to use the new API directly. For edge cases like empty mappings, the new API handles them differently.
I'll adapt the tests to verify the new behavior.

Let me now think about what happens for tests that use mapping_files. The cleanest approach is:

```python
  from CopySVGTranslation.io.mapping_store import MappingStore

  store = MappingStore()
  mapping = store.load_many([mapping_path])
  # or for single: mapping = store.load(mapping_path)

  service = SVGTranslationService(...)
  result = service.inject(svg_path=..., mapping=mapping, output=..., save=True)
```

But for the test test_inject_invalid_json_mapping, the legacy returns None because load_many fails to parse JSON and
returns empty, then legacy returns (None, {"error": ...}). With the new API, I'd need to handle this differently.

Let me now start writing all the changes. I'll go file by file.

Actually, wait. Let me also check what happens when save_path is provided but save_result is NOT explicitly True in
the legacy. For example:

```python
  tree = inject_file_tree(
      inject_file=svg_path,
      mapping=mappings,
      save_path=out_dir / "test.svg",
  )
```

In the legacy:

```python
  save_result=save_result or bool(save_path)  # → True because save_path is set
```

So save_result becomes True. The file gets saved.

In the new API:

```python
  result = service.inject(svg_path=svg_path, mapping=mappings, output=out_dir / "test.svg", save=True)
```

OK let me also think about the test_inject_with_empty_mapping_list_raises test:

```python
  with pytest.raises(TypeError) as excinfo:
      result = inject_file_tree(inject_file=target_svg, mapping_files=[])
```

The TypeError comes from TranslationMapping.from_any(None). With the new API:

```python
  service = SVGTranslationService()
  with pytest.raises(TypeError):
      service.inject(svg_path=target_svg, mapping=None, save=False)
```

Wait, but the original test says mapping_files=[] and the condition if not mapping and mapping_files is False because
[] is falsy. So mapping stays None and TranslationMapping.from_any(None) raises TypeError.

With the new API, I just need to pass None as mapping:

```python
  service = SVGTranslationService()
  with pytest.raises(TypeError):
      service.inject(svg_path=target_svg, mapping=None)
```

Actually wait, does service.inject have type checking that would prevent None? Let me check the signature:

```python
  def inject(self, svg_path, mapping: TranslationMapping | Mapping[str, Any], *, output=None, save=None):
```

Type hints don't enforce at runtime, so None would still get through to TranslationMapping.from_any(None) which raises
TypeError.

OK, now I'm ready to write all the changes. Let me go file by file.

Actually, one more thing: many tests in the legacy use extract() from CopySVGTranslation.legacy.extract. The plan only
mentions replacing inject_file_tree, not extract. So I'll leave extract calls as-is and only change the
inject_file_tree calls.

Let me also think about the save_path=file case where the test reads the file back to verify content was saved. The
new API with output=file, save=True should produce the same result.

Now, regarding pretty_print and sort_switches: these are config options. Let me verify:

-   TranslationConfig(pretty_print=True) → yes, it's a config option
-   TranslationConfig(sort_switches=True) → yes, it's a config option

Good. Now let me write all the files.

Let me start with the simpler files and work my way up.

### File 1: tests/e2e/injection/test_language_tracking.py

```python
  import textwrap
  from pathlib import Path

  from CopySVGTranslation import SVGTranslationService, TranslationConfig
  from CopySVGTranslation.core.mapping import InjectorData
  from CopySVGTranslation.utils.xml import tree_languages


  def write_svg(tmp_path: Path, content: str) -> Path:
      svg_path = tmp_path / "sample.svg"
      svg_path.write_text(textwrap.dedent(content), encoding="utf-8")
      return svg_path


  def test_inject_tracks_new_languages(tmp_path):
      svg_path = write_svg(tmp_path, """...""")
      mapping = {"new": {"hello": {"ar": "مرحبا", "fr": "Bonjour"}}}

      service = SVGTranslationService()
      result = service.inject(svg_path=svg_path, mapping=mapping, output=svg_path)

      assert result.success
      assert isinstance(result.data, InjectorData)
      tree = result.data.tree
      stats = result.data.inject_stats.to_json()

      after_languages = tree_languages(tree)
      assert after_languages == {"ar", "fr"}
      assert stats["all_languages_count"] == 2
      assert stats["new_languages_count"] == 2
      assert stats["languages_after"] == ["ar", "fr"]


  def test_inject_tracks_only_truly_new_languages(tmp_path):
      svg_path = write_svg(tmp_path, """...""")
      mapping = {"new": {"hello": {"ar": "مرحبا جديد", "fr": "Bonjour"}}}

      service = SVGTranslationService()
      result = service.inject(svg_path=svg_path, mapping=mapping, output=svg_path)

      assert result.success
      stats = result.data.inject_stats.to_json()

      assert stats["all_languages_count"] == 2
      assert stats["new_languages_count"] == 1
      assert stats["languages_after"] == ["fr"]


  def test_file_langs_handles_element_tree(tmp_path):
      svg_path = write_svg(tmp_path, """...""")

      service = SVGTranslationService()
      result = service.inject(
          svg_path=svg_path,
          mapping={"new": {"hello": {"ar": "مرحبا"}}},
          output=svg_path,
      )

      assert result.success
      tree = result.data.tree
      assert tree_languages(tree) == {"ar"}
```

### File 2: tests/e2e/injection/test_inject_extended.py

```python
  from CopySVGTranslation import SVGTranslationService, TranslationConfig
  from CopySVGTranslation.core.mapping import InjectorData


  class TestInjectEdgeCases(TestSetup):
      def test_inject_with_invalid_svg_structure(self):
          # ...setup...
          service = SVGTranslationService()
          result = service.inject(svg_path=svg_path, mapping=mappings, output=svg_path)

          assert not result.success  # instead of result is None + "error" in stats

      def test_inject_case_insensitive_false(self):
          # ...setup...
          service = SVGTranslationService(TranslationConfig(case_insensitive=False))
          result = service.inject(svg_path=svg_path, mapping=mappings, output=svg_path)
          assert result.success
          assert result.data.tree is not None

      def test_inject_save_result_creates_output_file(self):
          # ...setup...
          service = SVGTranslationService()
          result = service.inject(svg_path=svg_path, mapping=mappings, output=_output_file, save=True)
          assert _output_file.exists()
```

Wait, for test_inject_with_invalid_svg_structure, the old test asserts:

```python
  assert result is None
  assert "error" in stats
```

With the new API, when injection fails, result.success is False and result.data might be None or have error info. Let
me check what happens with an invalid SVG. The service catches the exception:

```python
  except Exception as exc:
      return OperationResult.fail(error=str(exc), error_code=...)
```

So result.success == False, result.data == None, result.error is set. The test becomes:

```python
  assert not result.success
  assert result.error is not None
```

But wait, the old test had result is None for the tree part. Let me look at the SVG:

```xml
  <svg xmlns="http://www.w3.org/2000/svg">
      <text id="bad|id">Test</text>
  </svg>
```

This has no <switch> element, so it might just succeed with no changes rather than failing. Let me think...

Actually, the injector prepares the SVG first. The preparer wraps texts in switches if needed. Let me check what
happens with bad|id. Looking at the injector code would be complex. Let me just check: with the legacy, the result was
(None, {"error": "..."}). This means the injection failed. With the new API, result.success should be False.

Actually, I realize I should just test this. But since I'm making changes, let me trust the pattern and write:

```python
  assert not result.success or result.data is None
```

No wait, that's too loose. Let me use:

```python
  # The injection should fail for invalid SVG structure
  if result.success:
      # If it somehow succeeds, the tree should at least be valid
      assert result.data.tree is not None
  else:
      assert result.error is not None
```

Actually, that's too complex. Let me just check what the legacy returns and match the behavior. The legacy returns
(None, {"error": "..."}) when the service fails. So with the new API:

```python
  assert not result.success
```

This should be equivalent. The old test checks result is None (tree is None) and "error" in stats. With new API,
result.success == False covers both cases.

Hmm, but actually... let me look at the service code more carefully:

```python
  if injector_data.tree is None:
      return OperationResult.fail(
          error=injector_data.error.label or "Injection returned no tree",
          error_code=injector_data.error.code or "injection_failed",
          stats=injector_data.inject_stats,
      )
```

So when tree is None, the service returns fail. Good.

But there's also the case where the exception is caught:

```python
  except Exception as exc:
      return OperationResult.fail(error=str(exc), error_code=...)
```

Either way, result.success == False.

OK let me just write assert not result.success for error cases.

Actually, for the test_inject_with_invalid_svg_structure test, I realize I need to also check the equivalent of
"error" in stats. Let me just check result.error is not None or result.error_code is not None.

Let me now write all the files. I'll be systematic.

Actually, let me reconsider the approach for test_inject_with_empty_mapping_list_raises in test_public_api.py. The
test expects TypeError. With the new API:

```python
  service = SVGTranslationService()
  with pytest.raises(TypeError):
      service.inject(svg_path=target_svg, mapping=None)
```

Wait, but inject has save=None which defaults to config.auto_save which defaults to False. So no output needed. But
mapping=None would cause TranslationMapping.from_any(None) to raise TypeError. Let me verify:

```python
  @classmethod
  def from_any(cls, data):
      if isinstance(data, TranslationMapping):
          return data
      data_json = data
      if not isinstance(data_json, dict) and not isinstance(data_json, Mapping):
          raise TypeError(f"Expected Mapping/TranslationMapping/dict, got {type(data_json)}")
```

Yes, None → not dict, not Mapping → raises TypeError. Good.

OK one more consideration. For tests that use mapping_files, I need to load the mapping before calling inject. I'll
use MappingStore. But I need to import it. Let me check if it's exported from the package... Looking at **init**.py:

```python
  __all__ = [
      "CopySVGTranslationError",
      "NestedTspanDetector",
      ...
      "SVGTranslationService",
      "TranslationConfig",
      "TranslationEntry",
      "TranslationMapping",
  ]
```

MappingStore is NOT in the public API. So I should import it directly from its module:

```python
  from CopySVGTranslation.io.mapping_store import MappingStore
```

OK, now let me write everything. I'll go file by file, starting with the simplest ones.

Actually, I realize I should think about whether to keep the extract calls or change them too. The plan only mentions
inject_file_tree. Looking at the test files, many use both extract and inject_file_tree. The extract function is also
from the legacy module. Let me check if there's a plan for extract too...

Looking at the service, it has service.extract() which returns OperationResult[TranslationMapping]. But the plan only
mentions replacing inject_file_tree. And the extract legacy function is still used in many tests (including ones that
don't use inject_file_tree). So I'll only change the inject_file_tree calls and leave extract calls alone.

For tests that do translations = extract(...) and then inject_file_tree(mapping=translations, ...), the extract
returns a dict which is compatible with service.inject(mapping=dict).

OK, now I need to decide about import style. Should I use:

```python
  from CopySVGTranslation import SVGTranslationService, TranslationConfig
```

or

```python
  from CopySVGTranslation.service import SVGTranslationService
  from CopySVGTranslation.config import TranslationConfig
```

I'll use the public API import: from CopySVGTranslation import SVGTranslationService, TranslationConfig

For InjectorData: from CopySVGTranslation.core.mapping import InjectorData
For MappingStore: from CopySVGTranslation.io.mapping_store import MappingStore

Let me now write all the files. Let me organize the changes:

### Files to modify (12 test files):

1.  tests/e2e/extraction/test_extract.py - 2 calls
2.  tests/e2e/injection/test_inject2.py - 2 calls
3.  tests/e2e/injection/test_inject_extended.py - 3 calls
4.  tests/e2e/injection/test_language_tracking.py - 3 calls
5.  tests/e2e/legacy/test_additional.py - 3 calls
6.  tests/e2e/legacy/test_comprehensive.py - 2 calls (3rd already migrated)
7.  tests/e2e/legacy/test_full.py - 7 calls
8.  tests/e2e/svg_translate/test_svgtranslate.py - 5 calls
9.  tests/e2e/svg_translate/test_svgtranslate_extended.py - 8 calls
10. tests/e2e/test_manual_workflows.py - 1 call
11. tests/e2e/test_public_api.py - 2 calls
12. tests/unit/test_examples.py - 1 call

### Files to potentially clean up (imports only):

13. tests/unit/injection/test_worker.py - just import
14. tests/unit/legacy/test_injection_worker.py - just import + TODO

Let me start writing. I'll do this efficiently with multiple edits per file.

Let me re-examine the test_inject_basic_workflow test in test_additional.py more carefully:

```python
  def test_inject_basic_workflow(self, temp_dir):
      """Test basic inject workflow."""
      target = temp_dir / "target.svg"
      content = """..."""
      target.write_text(content, encoding="utf-8")
      translations = {"new": {"hi": {"ar": "مرحبا"}}}
      tree, stats = inject_file_tree(
          mapping=translations,
          inject_file=target,
          return_stats=True,
          save_result=True,
      )
      assert tree is None
```

This calls with save_result=True but no save_path. The legacy function passes save_result=True to the service, which
has auto_save=False in config, but save=True override. Since output=None and save=True, the service returns fail. The
legacy then returns (None, {"error": "error"}).

With the new API:

```python
  service = SVGTranslationService()  # auto_save=False by default
  result = service.inject(svg_path=target, mapping=translations, save=True)
  # save=True but no output → fail
  assert not result.success
```

Wait, but this test is titled "test_inject_basic_workflow" and asserts tree is None. That seems like it's testing
error handling, not a basic workflow. Let me just convert it faithfully.

OK, let me also consider: when the service fails, result.data is None. So there's no result.data.tree or
result.data.inject_stats. I need to handle this in tests that check stats on potentially failing calls.

Now let me actually start writing the changes. I'll do all the files.

For test_inject_nonexistent_file in test_svgtranslate.py:

```python
  def test_inject_nonexistent_file(self):
      nonexistent_path = self.test_dir / "nonexistent.svg"
      mapping_path = self.test_dir / "arabic.svg.json"
      with open(mapping_path, "w", encoding="utf-8") as f:
          json.dump(self.expected_translations, f, ensure_ascii=False)
      result = inject_file_tree(inject_file=nonexistent_path, mapping_files=[mapping_path])
      assert result is None
```

New API:

```python
  def test_inject_nonexistent_file(self):
      nonexistent_path = self.test_dir / "nonexistent.svg"
      mapping_path = self.test_dir / "arabic.svg.json"
      with open(mapping_path, "w", encoding="utf-8") as f:
          json.dump(self.expected_translations, f, ensure_ascii=False)

      store = MappingStore()
      mapping = store.load(mapping_path)
      service = SVGTranslationService()
      result = service.inject(svg_path=nonexistent_path, mapping=mapping, output=nonexistent_path)
      assert not result.success
```

For test_inject_nonexistent_mapping:

```python
  def test_inject_nonexistent_mapping(self):
      svg_path = self.test_dir / "test.svg"
      nonexistent_mapping = self.test_dir / "nonexistent.json"
      with open(svg_path, "w", encoding="utf-8") as f:
          f.write(self.no_translations_svg_content)
      assert svg_path.exists()
      result = inject_file_tree(inject_file=svg_path, mapping_files=[nonexistent_mapping])
      # assert result is None
```

Note the assertion is commented out! So the test just checks it doesn't crash. With the new API:

```python
  def test_inject_nonexistent_mapping(self):
      svg_path = self.test_dir / "test.svg"
      nonexistent_mapping = self.test_dir / "nonexistent.json"
      with open(svg_path, "w", encoding="utf-8") as f:
          f.write(self.no_translations_svg_content)
      assert svg_path.exists()

      store = MappingStore()
      mapping = store.load_many([nonexistent_mapping])  # returns empty mapping
      service = SVGTranslationService()
      result = service.inject(svg_path=svg_path, mapping=mapping, output=svg_path)
      # With empty mapping, injection succeeds but does nothing
      assert result.success
```

Actually, load_many with nonexistent file just logs a warning and returns empty mapping. Then inject with empty
mapping succeeds (no switches processed). So the behavior is different from legacy. But the assertion in legacy is
commented out, so it's not really testing anything specific. I'll adapt it to match new behavior.

For test_inject_empty_mapping_file in test_svgtranslate_extended.py:

```python
  def test_inject_empty_mapping_file(self):
      empty_mapping = {"new": {}}
      mapping_path = self.test_dir / "empty_mapping.json"
      with open(mapping_path, "w", encoding="utf-8") as f:
          json.dump(empty_mapping, f)
      _path = self.test_dir / "target.svg"
      with open(_path, "w", encoding="utf-8") as f:
          f.write(self.no_translations_svg_content)
      tree, stats = inject_file_tree(inject_file=_path, mapping_files=[mapping_path], return_stats=True)
      assert tree is None
      assert stats == {"error": "No valid mappings found"}
```

With the legacy, load_many loads the file, gets {"new": {}}, creates a TranslationMapping where new={}. Then
is_empty() returns True (no new entries and no title_new). Legacy returns (None, {"error": "No valid mappings
found"}).

With the new API, store.load(path) would return a TranslationMapping with empty new. Then service.inject() with this
empty mapping... let me check:

```python
  normalized = TranslationMapping.from_any(mapping)
  injector_data = self._injector.inject(svg_path, normalized, ...)
```

The injector would process switches but find no matching translations, so it would return success with 0 processed
switches. Actually, looking at the service:

```python
  if injector_data.tree is None:
      return OperationResult.fail(...)
  return OperationResult.ok(data=injector_data, stats=injector_data.inject_stats)
```

So it would return success with an InjectorData that has 0 stats. This is different from the legacy behavior.

For this test, I need to decide: should I check is_empty() first (replicating legacy behavior) or accept the new
behavior? Since we're migrating to the new API, I'll accept the new behavior:

```python
  def test_inject_empty_mapping_file(self):
      empty_mapping = {"new": {}}
      mapping_path = self.test_dir / "empty_mapping.json"
      with open(mapping_path, "w", encoding="utf-8") as f:
          json.dump(empty_mapping, f)
      _path = self.test_dir / "target.svg"
      with open(_path, "w", encoding="utf-8") as f:
          f.write(self.no_translations_svg_content)

      store = MappingStore()
      mapping = store.load(mapping_path)
      assert mapping.is_empty()

      service = SVGTranslationService()
      result = service.inject(svg_path=_path, mapping=mapping, output=_path)
      assert result.success
      stats = result.data.inject_stats.to_json()
      assert stats["processed_switches"] == 0
      assert stats["inserted_translations"] == 0
```

Hmm, but the old test asserts tree is None and error in stats. The new behavior is different. Let me keep the test
meaningful by checking that the mapping is empty and that injection with empty mapping produces zero stats.

For test_inject_invalid_json_mapping:

```python
  def test_inject_invalid_json_mapping(self):
      mapping_path = self.test_dir / "invalid.json"
      with open(mapping_path, "w", encoding="utf-8") as f:
          f.write("{invalid json content")
      _path = self.test_dir / "target.svg"
      with open(_path, "w", encoding="utf-8") as f:
          f.write(self.no_translations_svg_content)
      result = inject_file_tree(inject_file=_path, mapping_files=[mapping_path])
      assert result is None
```

With the new API, store.load(path) would raise json.JSONDecodeError. I should catch this:

```python
  def test_inject_invalid_json_mapping(self):
      mapping_path = self.test_dir / "invalid.json"
      with open(mapping_path, "w", encoding="utf-8") as f:
          f.write("{invalid json content")
      _path = self.test_dir / "target.svg"
      with open(_path, "w", encoding="utf-8") as f:
          f.write(self.no_translations_svg_content)

      store = MappingStore()
      with pytest.raises(json.JSONDecodeError):
          store.load(mapping_path)
```

Or using load_many which catches exceptions:

```python
  mapping = store.load_many([mapping_path])
  # load_many catches JSONDecodeError, logs error, returns empty mapping
  assert mapping.is_empty()
```

I'll use load_many for consistency with how the legacy handled it (it also used load_many):

```python
  store = MappingStore()
  mapping = store.load_many([mapping_path])
  # load_many skips files that fail to parse, resulting in empty mapping
  assert mapping.is_empty()

  service = SVGTranslationService()
  result = service.inject(svg_path=_path, mapping=mapping, output=_path)
  assert result.success  # empty mapping still succeeds, just no changes
```

Actually wait, let me check how load_many handles JSON errors:

```python
  def load_many(self, paths):
      result = TranslationMapping()
      for p in paths:
          try:
              result.merge(self.load(p))
          except FileNotFoundError:
              logger.warning(...)
          except Exception as exc:
              logger.error(...)
      return result
```

Yes, it catches all exceptions (including JSONDecodeError) and continues. So the result is an empty mapping.

OK, I think I have enough understanding now. Let me start making the edits. I'll work through the files
systematically.

Let me also think about the test_inject_with_empty_mapping_list_raises test:

```python
  def test_inject_with_empty_mapping_list_raises(self, tmp_path, fixtures_dir):
      target_svg = tmp_path / "target.svg"
      target_svg.write_text(...)
      with pytest.raises(TypeError) as excinfo:
          result = inject_file_tree(inject_file=target_svg, mapping_files=[])
```

The legacy behavior: mapping_files=[] → condition not mapping and mapping_files is False (empty list) → mapping stays
None → TranslationMapping.from_any(None) → TypeError.

With new API, we wouldn't use mapping_files at all. The test becomes about passing None as mapping:

```python
  def test_inject_with_none_mapping_raises(self, tmp_path, fixtures_dir):
      target_svg = tmp_path / "target.svg"
      target_svg.write_text(...)
      service = SVGTranslationService()
      with pytest.raises(TypeError):
          service.inject(svg_path=target_svg, mapping=None)
```

OK let me now write everything. Let me start.

Wait, one more thing. For test_inject_without_stats in test_full.py:

```python
  def test_inject_without_stats(tmp_path, target_svg, fixtures_dir):
      translations = extract(fixtures_dir / "source.svg")
      result = inject_file_tree(
          inject_file=target_svg,
          mapping=translations,
          return_stats=False,
      )
      assert result is not None
```

With return_stats=False, the legacy returns just tree (not a tuple). With the new API:

```python
  service = SVGTranslationService()
  result = service.inject(svg_path=target_svg, mapping=translations, output=target_svg)
  assert result.success
  assert result.data is not None
  assert result.data.tree is not None
```

OK, now let me really start writing. I'll do the files in order.

Let me think about a good approach. Since many files have similar patterns, let me define a clear conversion for each
pattern and apply them consistently.

Conversion patterns:

P1: Simple inject with mapping dict, return_stats=True

```python
  # Old:
  tree, stats = inject_file_tree(inject_file=svg_path, mapping=mappings, return_stats=True)
  # New:
  service = SVGTranslationService()
  result = service.inject(svg_path=svg_path, mapping=mappings, output=svg_path)
  assert result.success
  tree = result.data.tree
  stats = result.data.inject_stats.to_json()
```

P2: Simple inject with mapping dict, no return_stats

```python
  # Old:
  tree = inject_file_tree(inject_file=svg_path, mapping=mappings)
  # New:
  service = SVGTranslationService()
  result = service.inject(svg_path=svg_path, mapping=mappings, output=svg_path)
  assert result.success
  tree = result.data.tree
```

P3: Inject with save_path

```python
  # Old:
  tree = inject_file_tree(inject_file=svg_path, mapping=mappings, save_path=output_path)
  # New:
  service = SVGTranslationService()
  result = service.inject(svg_path=svg_path, mapping=mappings, output=output_path, save=True)
  assert result.success
  tree = result.data.tree
```

P4: Inject with case_insensitive=False

```python
  service = SVGTranslationService(TranslationConfig(case_insensitive=False))
```

P5: Inject with overwrite_translations=True

```python
  service = SVGTranslationService(TranslationConfig(overwrite_translations=True))
```

P6: Inject with mapping_files

```python
  # Old:
  tree, stats = inject_file_tree(inject_file=svg_path, mapping_files=[path], return_stats=True)
  # New:
  store = MappingStore()
  mapping = store.load_many([path])
  service = SVGTranslationService()
  result = service.inject(svg_path=svg_path, mapping=mapping, output=svg_path)
  tree = result.data.tree
  stats = result.data.inject_stats.to_json()
```

P7: Inject with multiple config options

```python
  service = SVGTranslationService(TranslationConfig(
      overwrite_translations=True,
      pretty_print=True,
  ))
```

Now let me write all the files. I'll use edit for existing files.

Actually, there are also some tests in test_comprehensive.py and test_full.py that use the legacy extract function to
prepare the mapping before injection. Since I'm only migrating inject_file_tree, I'll leave the extract calls as-is
and just convert the injection part. The extract function returns a dict that's compatible with
service.inject(mapping=dict).

Let me also double-check: when extract() returns a dict like {"new": {...}, "tspans_by_id": {...}, ...}, does
TranslationMapping.from_any() handle it? Yes:

```python
  @classmethod
  def from_any(cls, data):
      if isinstance(data, TranslationMapping):
          return data
      return cls(
          new=dict(data.get("new", {})),
          title_new=dict(data.get("title_new", {})),
          tspans_by_id=dict(data.get("tspans_by_id", {})),
          meta=dict(data.get("meta", {})),
          error=data.get("error", ""),
      )
```

Good, it handles the full dict format.

Now let me start. I'll do the simplest files first.

For tests/unit/injection/test_worker.py and tests/unit/legacy/test_injection_worker.py, they just import
inject_file_tree with no actual tests. I'll update the imports but leave the files as stubs.

Actually, test_worker.py:

```python
  from CopySVGTranslation.legacy.inject import (
      inject_file_tree,
  )
```

This is just an import with no tests. I could either remove the import or update it. Since it's just a stub, I'll
update the import to use the new API:

```python
  from CopySVGTranslation import SVGTranslationService
```

Similarly for test_injection_worker.py:

```python
  from CopySVGTranslation.legacy.inject import inject_file_tree
```

→

```python
  from CopySVGTranslation import SVGTranslationService
```
