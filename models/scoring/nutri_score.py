"""Nutri Score calculation.

This module implements a simplified version of the Nutri Score algorithm. It
computes negative points for energy, sugars, saturated fat and sodium, and
positive points for fibre, protein and the percentage of fruits/vegetables.
The final score is the total negative points minus the total positive points.
This score is then mapped to a letter grade from A (best) to E (worst).

The implementation here follows the general guidance of the FSA/FFSA nutrient
profiling system but omits the special cases for cheese, fats and beverages.
It is intended as a starting point; you should refer to the official
documentation for production use.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class NutriScoreResult:
    """Encapsulates the numeric score and the letter grade."""

    score: int
    grade: str


def _points_energy(kcal: float) -> int:
    """Assign negative points based on energy (kcal per 100 g)."""
    # thresholds approximate 335, 670, 1005... kJ converted to kcal
    thresholds = [80, 160, 240, 320, 400, 480, 560, 640, 720, 800]
    points = 0
    for idx, limit in enumerate(thresholds, start=1):
        if kcal > limit:
            points = idx
        else:
            break
    return points


def _points_sugars(sugars_g: float) -> int:
    """Assign negative points based on sugars (g per 100 g)."""
    limits = [4.5, 9.0, 13.5, 18.0, 22.5, 27.0, 31.0, 36.0, 40.0, 45.0]
    points = 0
    for idx, limit in enumerate(limits, start=1):
        if sugars_g > limit:
            points = idx
        else:
            break
    return points


def _points_sat_fat(sat_fat_g: float) -> int:
    """Assign negative points based on saturated fat (g per 100 g)."""
    limits = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    points = 0
    for idx, limit in enumerate(limits, start=1):
        if sat_fat_g > limit:
            points = idx
        else:
            break
    return points


def _points_sodium(sodium_mg: float) -> int:
    """Assign negative points based on sodium (mg per 100 g)."""
    limits = [90, 180, 270, 360, 450, 540, 630, 720, 810, 900]
    points = 0
    for idx, limit in enumerate(limits, start=1):
        if sodium_mg > limit:
            points = idx
        else:
            break
    return points


def _points_fibre(fibre_g: float) -> int:
    """Assign positive points based on fibre (g per 100 g)."""
    limits = [0.9, 1.9, 2.8, 3.7, 4.7]
    points = 0
    for idx, limit in enumerate(limits, start=1):
        if fibre_g >= limit:
            points = idx
        else:
            break
    return points


def _points_protein(protein_g: float) -> int:
    """Assign positive points based on protein (g per 100 g)."""
    limits = [1.6, 3.2, 4.8, 6.4, 8.0]
    points = 0
    for idx, limit in enumerate(limits, start=1):
        if protein_g >= limit:
            points = idx
        else:
            break
    return points


def _points_fvnl(pct_fvnl: float) -> int:
    """Assign positive points for fruits, vegetables, nuts and legumes (%)."""
    if pct_fvnl > 80:
        return 5
    elif pct_fvnl > 60:
        return 2
    elif pct_fvnl > 40:
        return 1
    return 0


def compute_nutri_score(nutrients: Dict[str, float]) -> NutriScoreResult:
    """Compute the Nutri Score from nutrient values.

    Parameters
    ----------
    nutrients:
        Dictionary with nutrient values per 100 g. Expected keys include
        ``energy_kcal_100g`` (kcal), ``sugars_100g`` (g), ``sat_fat_100g`` (g),
        ``sodium_100g`` (mg), ``fibre_100g`` (g), ``protein_100g`` (g), and
        ``fvnl_percent`` (%). Missing keys default to 0.

    Returns
    -------
    NutriScoreResult
        Contains the numeric score (negative minus positive points) and the
        corresponding letter grade.
    """
    energy = float(nutrients.get("energy_kcal_100g", 0))
    sugars = float(nutrients.get("sugars_100g", 0))
    sat_fat = float(nutrients.get("sat_fat_100g", 0))
    sodium = float(nutrients.get("sodium_100g", 0))
    fibre = float(nutrients.get("fibre_100g", 0))
    protein = float(nutrients.get("protein_100g", 0))
    fvnl_pct = float(nutrients.get("fvnl_percent", 0))

    n_points = (
        _points_energy(energy)
        + _points_sugars(sugars)
        + _points_sat_fat(sat_fat)
        + _points_sodium(sodium)
    )

    p_points = _points_fibre(fibre) + _points_protein(protein) + _points_fvnl(fvnl_pct)

    total = n_points - p_points

    # Map numeric score to grade according to classic thresholds
    if total <= -1:
        grade = "A"
    elif total <= 2:
        grade = "B"
    elif total <= 10:
        grade = "C"
    elif total <= 18:
        grade = "D"
    else:
        grade = "E"

    return NutriScoreResult(score=total, grade=grade)
