# apps/api/main.py
from fastapi import FastAPI, Query, HTTPException
from typing import Dict, Any
import dataclasses, json

from models.scoring.nutri_score import compute_nutri_score
from models.scoring.eco_score import compute_eco_score  # stub

app = FastAPI(title="NutriScan API")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

def _to_plain(x):
    """Make anything JSON-serializable for FastAPI."""
    if dataclasses.is_dataclass(x):
        return dataclasses.asdict(x)
    if hasattr(x, "model_dump"):         # pydantic v2
        return x.model_dump()
    if hasattr(x, "dict"):               # pydantic v1
        return x.dict()
    try:
        json.dumps(x)
        return x
    except TypeError:
        return json.loads(json.dumps(x, default=str))

@app.get("/products/{barcode}")
def get_product(
    barcode: str,
    energy_kcal_100g: float = Query(...),
    sugars_100g: float = Query(...),
    sat_fat_100g: float = Query(...),
    sodium_100g: float = Query(...),
    fibre_100g: float = Query(...),
    protein_100g: float = Query(...),
    fvnl_percent: float = Query(...)
) -> Dict[str, Any]:
    nutrients = {
        "energy_kcal_100g": energy_kcal_100g,
        "sugars_100g": sugars_100g,
        "sat_fat_100g": sat_fat_100g,
        "sodium_100g": sodium_100g,
        "fibre_100g": fibre_100g,
        "protein_100g": protein_100g,
        "fvnl_percent": fvnl_percent,
    }
    try:
        nutri = compute_nutri_score(nutrients)        # may return object or dict
        eco   = compute_eco_score(nutrients)            # stub may return object/dict
        return {
            "barcode": barcode,
            "nutrients": nutrients,
            "nutri_score": _to_plain(nutri),
            "eco_score": _to_plain(eco),
        }
    except Exception as e:
        # surface a clean 400 instead of a 500 if inputs are bad
        raise HTTPException(status_code=400, detail=f"scoring_failed: {type(e).__name__}: {e}")
