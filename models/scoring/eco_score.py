"""Eco Score calculation.

This module provides a very simple placeholder implementation of the
Eco Score algorithm. The real Eco Score methodology is based on a
life cycle analysis (PEF) combined with bonuses and maluses related
to farming practices, origin, packaging and the presence of threatened
species. Implementing the full method would require rich datasets and
external dependencies.  To keep this project self‑contained and runnable
offline, we provide a stubbed version here.

The `compute_eco_score` function accepts a dictionary of product
attributes and returns a numeric score, a letter grade (A–E) and a
confidence level.  By default it assigns a mid‑range score with low
confidence, but developers can extend this logic using the available
attributes (e.g., organic labels, origin distance, packaging material).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class EcoScoreResult:
    """Container for Eco Score results.

    Attributes
    ----------
    score:
        A numeric score on a 0‑100 scale. Lower scores indicate better
        ecological impact. In this simplified implementation the score
        always defaults to 50.
    grade:
        A letter grade from A (best) to E (worst) derived from the
        numeric score. A real implementation would map ranges of the
        PEF score to these letters.
    confidence:
        A float between 0 and 1 indicating how confident the system is
        in the computed grade. Because this stub does not use real
        environmental data the confidence defaults to 0.5.
    """

    score: int
    grade: str
    confidence: float


def compute_eco_score(product: Dict[str, Any]) -> EcoScoreResult:
    """Compute an Eco Score for a product.

    Parameters
    ----------
    product:
        A dictionary representing a product. Keys may include
        ``origin_country``, ``organic_flag``, ``packaging_material``, etc.
        The current implementation ignores these fields and returns a
        default score.

    Returns
    -------
    EcoScoreResult
        A stubbed eco score result with a fixed score, grade and
        confidence. Developers can extend this function to incorporate
        real environmental factors.
    """

    # Default score: mid‑range value. Real implementation would use
    # product attributes (origin, farming, packaging) to compute a
    # life‑cycle impact score and map it to A–E. Here we simply
    # return 50 which corresponds to a grade of "C".
    score = 50

    # Map the score to a grade. The mapping below is arbitrary and
    # intended to resemble the Nutri Score thresholds. You can adjust
    # these thresholds to better reflect ecological scoring if you have
    # more detailed data.
    if score <= 20:
        grade = "A"
    elif score <= 40:
        grade = "B"
    elif score <= 60:
        grade = "C"
    elif score <= 80:
        grade = "D"
    else:
        grade = "E"

    # Stub confidence: eco scores rely on many external datasets; in
    # this environment we can't fetch them so we signal low confidence.
    confidence = 0.5

    return EcoScoreResult(score=score, grade=grade, confidence=confidence)
