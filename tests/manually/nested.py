"""
python I:/SVG_PY/CopySVGTranslation/tests/manually/nested.py
"""
import sys
import logging
from pathlib import Path

logger = logging.getLogger("CopySVGTranslation")
logger.setLevel(logging.DEBUG)

console = logging.StreamHandler()
console.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
logger.addHandler(console)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySVGTranslation import inject, make_translation_ready
from CopySVGTranslation.injection import SvgNestedTspanException

svg_file = Path(__file__).parent / "test.svg"

svg_example = '''<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="850" height="721.1"
    viewBox="0 0 850 721.1"
    style="font-family: Lato, &quot;Helvetica Neue&quot;, Helvetica, Arial, &quot;Liberation Sans&quot;, sans-serif; text-rendering: geometricprecision; -webkit-font-smoothing: antialiased; font-size: 18px; background-color: rgb(255, 255, 255);">
    <g id="subtitle" class="markdown-text-wrap">
        <text x="16.0" y="66.5" fill="#5b5b5b"
            style="font-size: 15px; line-height: 1.2;">
            <tspan x="16" y="66.5">Estimated annual number of deaths attributed to <tspan
                    class="dod-span"
                    data-id="obesity">obesity<tspan style="font-feature-settings: &quot;sups&quot;;">
                ¹</tspan>
                </tspan> per 100,000 people.</tspan>
        </text>
    </g>
</svg>'''

svg_file.write_text(svg_example, encoding='utf-8')

data = {"new": {"lang none": {"la": "lang la (new)"}}}
try:
    make_translation_ready(svg_file, True)
except SvgNestedTspanException as e:
    print("SvgNestedTspanException")
    print(e.node())

# result = inject(inject_file=svg_file, all_mappings=data, save_result=True, overwrite=True, pretty_print=False)

# print(result)
