import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySVGTranslation import get_titles_translations

expected_data = {
    "parkinson's disease prevalence, 2028": {
        "pt": "Prevalência de doença de Parkinson, 2028",
        "es": "Prevalencia de la enfermedad de Parkinson, 2028",
        "ca": "Prevalència de la malaltia de Parkinson, 2028",
        "eu": "Parkinsonen gaixotasunaren prebalentzia, 2028",
        "cs": "Prevalence Parkinsonovy nemoci, 2028",
        "si": "පාකින්සන් රෝග ව්‍යාප්තිය, 2028",
        "ar": "انتشار مرض باركنسون، 2028"
    }
}
insert_data = {
    "parkinson's disease prevalence,": {
        "pt": "Prevalência de doença de Parkinson,",
        "es": "Prevalencia de la enfermedad de Parkinson,",
        "ca": "Prevalència de la malaltia de Parkinson,",
        "eu": "Parkinsonen gaixotasunaren prebalentzia,",
        "cs": "Prevalence Parkinsonovy nemoci,",
        "si": "පාකින්සන් රෝග ව්‍යාප්තිය,",
        "ar": "انتشار مرض باركنسون،"
    }
}
default_texts = [
    "parkinson's disease prevalence, 2028"
]

result = get_titles_translations(insert_data, default_texts)

print(json.dumps(result, indent=4, ensure_ascii=False))
