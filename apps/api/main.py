"""FastAPI service exposing product and score endpoints.

This microservice uses the in‑memory ``ProductDB`` to look up normalised
products, compute their scores on the fly and serve JSON responses.  Endpoints:

* ``GET /healthz`` – liveness check.
* ``GET /products/{barcode}`` – return a product card with nutrition per 100 g, scores and flags.
* ``GET /scores/{barcode}`` – return only the scoring breakdown for a product.
* ``POST /compare`` – compare two barcodes; returns a side‑by‑side diff of nutrients and scores.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

# When running this module with ``uvicorn``, ensure that the root of the
# repository is on ``PYTHONPATH`` so that `nutriscan_ai` can be imported.
from nutriscan_ai.packages.nutriscan_utils import (
    load_products,
    ProductDB,
    compute_scores_for_product,
)

app = FastAPI(title="NutriScan API", version="0.1.0")


class CompareRequest(BaseModel):
    barcodes: List[str]


class CompareResponse(BaseModel):
    products: Dict[str, Any]


# Initialise the product database and precompute scores on startup
_raw_products = load_products()
_db = ProductDB()
for product in _raw_products:
    scored = compute_scores_for_product(product)
    _db.upsert(scored)


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


@app.get("/products/{barcode}")
def get_product(barcode: str) -> Dict[str, Any]:
    """Return a product card with scores and flags.

    Raises
    ------
    HTTPException
        If the barcode is not found.
    """
    product = _db.get(barcode)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/scores/{barcode}")
def get_scores(barcode: str) -> Dict[str, Any]:
    """Return scoring breakdown for a product.

    Raises
    ------
    HTTPException
        If the barcode is not found.
    """
    product = _db.get(barcode)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.get("scores", {})


@app.post("/compare", response_model=CompareResponse)
def compare_products(req: CompareRequest) -> CompareResponse:
    """Compare two products by their barcodes.

    The request body must contain exactly two barcodes.  The response contains a
    dictionary mapping each barcode to its product card (or ``null`` if a
    barcode is unknown).
    """
    if len(req.barcodes) != 2:
        raise HTTPException(status_code=400, detail="Exactly two barcodes must be provided")
    barcode1, barcode2 = req.barcodes
    products = _db.compare(barcode1, barcode2)
    return CompareResponse(products=products)
