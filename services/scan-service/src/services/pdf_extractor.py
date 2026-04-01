"""
InBody PDF extractor using pdfplumber.
Extracts 24 standard metric keys from InBody scan PDFs via coordinate-based table parsing.
Returns a dict of {metric_key: float_value}. Missing keys are set to None.
"""
import io
import re
from typing import IO

import pdfplumber

from ..models.metric import STANDARD_METRIC_KEYS

# Patterns to locate metric values in extracted text
_PATTERNS = {
    "body_weight_kg": r"Body Weight\s+([\d.]+)\s*kg",
    "skeletal_muscle_mass_kg": r"Skeletal Muscle Mass\s+([\d.]+)\s*kg",
    "body_fat_mass_kg": r"Body Fat Mass\s+([\d.]+)\s*kg",
    "body_fat_percentage": r"(?:Percent Body Fat|Body Fat)\s+([\d.]+)\s*%",
    "fat_free_mass_kg": r"Fat.Free Mass\s+([\d.]+)\s*kg",
    "total_body_water_l": r"Total Body Water\s+([\d.]+)\s*[Ll]",
    "intracellular_water_l": r"Intracellular Water\s+([\d.]+)\s*[Ll]",
    "extracellular_water_l": r"Extracellular Water\s+([\d.]+)\s*[Ll]",
    "ecw_tbw_ratio": r"ECW/TBW\s+([\d.]+)",
    "protein_kg": r"Protein\s+([\d.]+)\s*kg",
    "minerals_kg": r"Minerals?\s+([\d.]+)\s*kg",
    "body_mass_index": r"BMI\s+([\d.]+)",
    "basal_metabolic_rate_kcal": r"(?:Basal Metabolic Rate|BMR)\s+([\d,]+)\s*kcal",
    "visceral_fat_level": r"Visceral Fat (?:Level|Area)\s+([\d.]+)",
    # Segmental lean
    "segmental_lean_right_arm_kg": r"Right Arm\s+([\d.]+)\s*kg",
    "segmental_lean_left_arm_kg": r"Left Arm\s+([\d.]+)\s*kg",
    "segmental_lean_trunk_kg": r"Trunk\s+([\d.]+)\s*kg",
    "segmental_lean_right_leg_kg": r"Right Leg\s+([\d.]+)\s*kg",
    "segmental_lean_left_leg_kg": r"Left Leg\s+([\d.]+)\s*kg",
}


def _safe_float(value: str) -> float | None:
    try:
        return float(value.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def extract_metrics(pdf_bytes: bytes) -> dict[str, float | None]:
    metrics: dict[str, float | None] = {k: None for k in STANDARD_METRIC_KEYS}

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    for key, pattern in _PATTERNS.items():
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            metrics[key] = _safe_float(match.group(1))

    # Segmental fat values — typically listed after lean values; extract with position context
    _extract_segmental_fat(full_text, metrics)

    return metrics


def _extract_segmental_fat(text: str, metrics: dict) -> None:
    """
    InBody reports list segmental fat data separately from lean mass.
    We look for a 'Fat' section and extract the 5 regional values in order:
    Right Arm, Left Arm, Trunk, Right Leg, Left Leg.
    """
    fat_section = re.search(
        r"(?:Segmental Fat Analysis|Fat\s+Mass)(.*?)(?:InBody Score|Nutritional|Visceral|$)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if not fat_section:
        return

    fat_text = fat_section.group(1)
    values = re.findall(r"([\d.]+)\s*kg", fat_text)
    keys = [
        "segmental_fat_right_arm_kg",
        "segmental_fat_left_arm_kg",
        "segmental_fat_trunk_kg",
        "segmental_fat_right_leg_kg",
        "segmental_fat_left_leg_kg",
    ]
    for i, key in enumerate(keys):
        if i < len(values):
            metrics[key] = _safe_float(values[i])
