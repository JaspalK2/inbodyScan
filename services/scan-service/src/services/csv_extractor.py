"""
InBody CSV extractor.

Handles the two CSV layouts exported by InBody devices:

  Layout A — tabular (multi-record, one scan per row):
      Row 0: header row with column names
      Row 1+: one record per row
      The row with the most recent date is selected; if no date column exists
      the first data row is used (InBody app exports newest-first).

  Layout B — key-value (single-record):
      Two columns: Measurement | Value

Returns:
  (metrics_dict, scan_date_str | None)
  scan_date_str is ISO "YYYY-MM-DD" when a date column is found.

Unit conversions applied automatically:
  lb  → kg  (× 0.453592)
  kJ  → kcal (÷ 4.184)
"""
from __future__ import annotations

import csv
import io
import re
from datetime import datetime
from typing import Optional

from ..models.metric import STANDARD_METRIC_KEYS

# ---------------------------------------------------------------------------
# Column-name → internal metric-key mapping (after stripping units/garbage)
# ---------------------------------------------------------------------------
_COL_MAP: dict[str, str] = {
    # Weight
    "weight": "body_weight_kg",
    "body weight": "body_weight_kg",
    # Muscle
    "skeletal muscle mass": "skeletal_muscle_mass_kg",
    "smm": "skeletal_muscle_mass_kg",
    "soft lean mass": "fat_free_mass_kg",   # InBody "Soft Lean Mass" ≈ fat-free mass
    # Fat
    "body fat mass": "body_fat_mass_kg",
    "bfm": "body_fat_mass_kg",
    "percent body fat": "body_fat_percentage",
    "pbf": "body_fat_percentage",
    "body fat": "body_fat_percentage",
    "body fat percent": "body_fat_percentage",
    "body fat percentage": "body_fat_percentage",
    # Lean / fat-free
    "fat-free mass": "fat_free_mass_kg",
    "fat free mass": "fat_free_mass_kg",
    "lean body mass": "fat_free_mass_kg",
    "lbm": "fat_free_mass_kg",
    # Water
    "total body water": "total_body_water_l",
    "tbw": "total_body_water_l",
    "intracellular water": "intracellular_water_l",
    "icw": "intracellular_water_l",
    "extracellular water": "extracellular_water_l",
    "ecw": "extracellular_water_l",
    "ecw/tbw": "ecw_tbw_ratio",
    "ecw tbw": "ecw_tbw_ratio",
    "ecw tbw ratio": "ecw_tbw_ratio",
    "ecw ratio": "ecw_tbw_ratio",           # InBody app column name
    # Composition
    "protein": "protein_kg",
    "minerals": "minerals_kg",
    "mineral": "minerals_kg",
    "bone mineral content": "minerals_kg",  # fallback for BMC
    # Indices / scores
    "bmi": "body_mass_index",
    "body mass index": "body_mass_index",
    "bmr": "basal_metabolic_rate_kcal",
    "basal metabolic rate": "basal_metabolic_rate_kcal",
    "visceral fat level": "visceral_fat_level",
    "visceral fat level": "visceral_fat_level",
    "vfl": "visceral_fat_level",
    "visceral fat area": "visceral_fat_level",
    "vfa": "visceral_fat_level",
    # Segmental lean — all 'left leg' variants (InBody has both cases)
    "right arm lean mass": "segmental_lean_right_arm_kg",
    "right arm lean": "segmental_lean_right_arm_kg",
    "ra lean": "segmental_lean_right_arm_kg",
    "left arm lean mass": "segmental_lean_left_arm_kg",
    "left arm lean": "segmental_lean_left_arm_kg",
    "la lean": "segmental_lean_left_arm_kg",
    "trunk lean mass": "segmental_lean_trunk_kg",
    "trunk lean": "segmental_lean_trunk_kg",
    "right leg lean mass": "segmental_lean_right_leg_kg",
    "right leg lean": "segmental_lean_right_leg_kg",
    "rl lean": "segmental_lean_right_leg_kg",
    "left leg lean mass": "segmental_lean_left_leg_kg",
    "left leg lean": "segmental_lean_left_leg_kg",
    "ll lean": "segmental_lean_left_leg_kg",
    # Segmental fat
    "right arm fat mass": "segmental_fat_right_arm_kg",
    "right arm fat": "segmental_fat_right_arm_kg",
    "ra fat": "segmental_fat_right_arm_kg",
    "left arm fat mass": "segmental_fat_left_arm_kg",
    "left arm fat": "segmental_fat_left_arm_kg",
    "la fat": "segmental_fat_left_arm_kg",
    "trunk fat mass": "segmental_fat_trunk_kg",
    "trunk fat": "segmental_fat_trunk_kg",
    "right leg fat mass": "segmental_fat_right_leg_kg",
    "right leg fat": "segmental_fat_right_leg_kg",
    "rl fat": "segmental_fat_right_leg_kg",
    "left leg fat mass": "segmental_fat_left_leg_kg",
    "left leg fat": "segmental_fat_left_leg_kg",
    "ll fat": "segmental_fat_left_leg_kg",
}

_DATE_COL_HINTS = {"date", "test date", "scan date", "measurement date", "datetime"}

# Strip unit suffix like (kg), (lb), (kJ), (cm²) — including garbled UTF-8
_STRIP_UNIT = re.compile(r"\s*\([^)]*\)\s*$")
# Remove any remaining non-ASCII/punctuation garbage after unit stripping
_STRIP_GARBAGE = re.compile(r"[^\w\s/\-]")


def _normalise_col(raw: str) -> tuple[str, str]:
    """
    Return (normalised_name, unit_lowercase).
    e.g. "Weight(lb)" → ("weight", "lb")
         "Basal Metabolic Rate(kJ)" → ("basal metabolic rate", "kj")
    """
    s = raw.strip().lower()
    unit_match = re.search(r"\(([^)]+)\)\s*$", s)
    unit = _STRIP_GARBAGE.sub("", unit_match.group(1)).strip() if unit_match else ""
    name = _STRIP_UNIT.sub("", s)
    name = _STRIP_GARBAGE.sub("", name).strip()
    return name, unit


def _convert(value: float, unit: str, metric_key: str) -> float:
    """Apply unit conversion so all stored values are in kg / L / kcal."""
    if unit == "lb":
        return value * 0.453592
    if unit in ("kj",) and "kcal" in metric_key:
        return value / 4.184
    return value


def _safe_float(v: str) -> Optional[float]:
    """Parse numeric string; return None for '-', empty, or non-numeric."""
    v = v.strip()
    if not v or v == "-":
        return None
    try:
        return float(v.replace(",", ""))
    except ValueError:
        return None


def _parse_date(v: str) -> Optional[str]:
    """
    Try common InBody date formats including the 14-digit timestamp
    (YYYYMMDDHHmmss) used by the InBody app CSV export.
    Returns ISO "YYYY-MM-DD" or None.
    """
    v = v.strip()
    # 14-digit compact timestamp: 20260105231602
    if re.fullmatch(r"\d{14}", v):
        try:
            return datetime.strptime(v, "%Y%m%d%H%M%S").date().isoformat()
        except ValueError:
            pass
    # 8-digit date: 20260105
    if re.fullmatch(r"\d{8}", v):
        try:
            return datetime.strptime(v, "%Y%m%d").date().isoformat()
        except ValueError:
            pass
    for fmt in (
        "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d",
        "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y %H:%M", "%d/%m/%Y %H:%M",
    ):
        try:
            return datetime.strptime(v, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _extract_tabular(rows: list[list[str]]) -> tuple[dict[str, Optional[float]], Optional[str]]:
    # Find header row
    header_idx = None
    for i, row in enumerate(rows):
        if any(_normalise_col(c)[0] in _COL_MAP or _normalise_col(c)[0] in _DATE_COL_HINTS
               for c in row):
            header_idx = i
            break

    if header_idx is None:
        return {k: None for k in STANDARD_METRIC_KEYS}, None

    parsed_headers: list[tuple[str, str]] = [_normalise_col(c) for c in rows[header_idx]]
    data_rows = [r for r in rows[header_idx + 1:] if any(c.strip() for c in r)]
    if not data_rows:
        return {k: None for k in STANDARD_METRIC_KEYS}, None

    # Find date column index
    date_col_idx: Optional[int] = next(
        (i for i, (name, _) in enumerate(parsed_headers) if name in _DATE_COL_HINTS),
        None,
    )

    # Select most-recent row: sort by date descending, fall back to first row
    if date_col_idx is not None:
        def _row_date(r: list[str]) -> str:
            cell = r[date_col_idx].strip() if date_col_idx < len(r) else ""
            return _parse_date(cell) or ""
        data_rows = sorted(data_rows, key=_row_date, reverse=True)

    values = data_rows[0]

    metrics: dict[str, Optional[float]] = {k: None for k in STANDARD_METRIC_KEYS}
    scan_date: Optional[str] = None

    for col_idx, (col_name, unit) in enumerate(parsed_headers):
        if col_idx >= len(values):
            break
        cell = values[col_idx].strip()

        if col_name in _DATE_COL_HINTS:
            scan_date = _parse_date(cell)
            continue

        metric_key = _COL_MAP.get(col_name)
        if metric_key:
            raw = _safe_float(cell)
            metrics[metric_key] = _convert(raw, unit, metric_key) if raw is not None else None

    return metrics, scan_date


def _extract_kv(rows: list[list[str]]) -> tuple[dict[str, Optional[float]], Optional[str]]:
    metrics: dict[str, Optional[float]] = {k: None for k in STANDARD_METRIC_KEYS}
    scan_date: Optional[str] = None

    for row in rows:
        if len(row) < 2:
            continue
        col_name, unit = _normalise_col(row[0])
        cell = row[1].strip()

        if col_name in _DATE_COL_HINTS:
            scan_date = _parse_date(cell)
            continue

        metric_key = _COL_MAP.get(col_name)
        if metric_key:
            raw = _safe_float(cell)
            metrics[metric_key] = _convert(raw, unit, metric_key) if raw is not None else None

    return metrics, scan_date


def _is_kv_layout(rows: list[list[str]]) -> bool:
    data = [r for r in rows if any(c.strip() for c in r)]
    if not data:
        return False
    if max(len(r) for r in data) > 3:
        return False
    matches = sum(
        1 for r in data
        if len(r) >= 1 and _normalise_col(r[0])[0] in _COL_MAP
    )
    return matches >= 3


def extract_from_csv(csv_bytes: bytes) -> tuple[dict[str, Optional[float]], Optional[str]]:
    """
    Parse an InBody CSV export.
    Returns (metrics_dict, scan_date_iso_or_None).
    """
    text = csv_bytes.decode("utf-8-sig", errors="replace")  # handle BOM
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)

    if _is_kv_layout(rows):
        return _extract_kv(rows)
    return _extract_tabular(rows)
