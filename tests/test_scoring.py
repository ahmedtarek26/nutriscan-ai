import pytest
from models.scoring.nutri_score import compute_nutri_score
from models.scoring.eco_score import compute_eco_score


def test_compute_nutri_score():
    assert compute_nutri_score({}) == "C"


def test_compute_eco_score():
    assert compute_eco_score({}) == "C"
