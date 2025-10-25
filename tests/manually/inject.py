"""
python I:/SVG_PY/CopySvgTranslate/tests/manually/inject.py
"""
import sys
import logging
from pathlib import Path

logger = logging.getLogger("CopySvgTranslate")
logger.setLevel(logging.DEBUG)

console = logging.StreamHandler()
console.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
logger.addHandler(console)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySvgTranslate import inject, make_translation_ready

svg_file = Path(__file__).parent / "test.svg"

svg_file.write_text(
    '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch id="testswitch"><text systemLanguage="la">lang la (1)</text><text systemLanguage="la">lang la (2)</text><text>lang none</text></switch></svg>''',
    encoding='utf-8',
)

data = {"new": {"lang none": {"la": "lang la (new)"}}}

make_translation_ready(svg_file, True)

result = inject(inject_file=svg_file, all_mappings=data, save_result=True, overwrite=True, pretty_print=False)

# print(result)
