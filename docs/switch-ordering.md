# Check and Fix Switch Ordering

For translations to render on Wikimedia Commons, every `<switch>` must keep its fallback `<text>` (the one without a `systemLanguage` attribute) **last** among its `<text>` children. Files where the fallback appears earlier will silently fail to show translations. Use the ordering check before re-uploading a file to Commons.

## Check whether switches are already sorted

`check_switches_sorted()` is read-only and returns `True` when every `<switch>` in the file is correctly ordered.

```python
from CopySVGTranslation import SVGTranslationService

service = SVGTranslationService()
result = service.check_switches_sorted("diagram.svg")

if result.success and not result.data:
    print("Switches are out of order — fix and re-upload.")
```

## Fix switches and save

`sort_switches()` reorders only when necessary and returns `True` if the file was actually modified (so you can decide whether a re-upload is needed).

```python
result = service.sort_switches(
    "diagram.svg",
    output="fixed/diagram.svg",
)

if result.success and result.data:
    print("File was modified; upload fixed/diagram.svg to Commons.")
```

If you omit `output`, the file is checked and reordered in memory only and `True` is still returned when a change would be required.
