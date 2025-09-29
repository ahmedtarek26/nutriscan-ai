"""Simplified retrieval‑augmented question answering service.

The full NutriScan blueprint calls for a sophisticated RAG system that indexes
normalised product facts, taxonomies and documentation, embeds them into a
vector space and uses a language model to answer arbitrary questions.  Due to
resource constraints and the lack of an external API, this implementation
takes a pragmatic approach:

* It loads the same sample dataset as the API service and stores it in a
  `ProductDB` instance.
* It inspects the incoming natural language question for a handful of known
  intents (vegan check, comparison, allergen lookup).
* It constructs a deterministic answer from the database and returns a
  JSON payload with the answer and a list of barcodes used as "citations".

While simplistic, this service demonstrates how to expose a `/ask` endpoint
that could later be replaced by a fully‑featured RAG pipeline once an LLM and
vector store are integrated.  In this version we add a minimal vector store
implementation based on TF‑IDF and nearest‑neighbour search.  When the
incoming query does not match any of the explicit patterns below, we fall
back to this approximate search to return the most similar products as
citations.  This keeps the API usable even without an LLM.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

import os
from pathlib import Path
import joblib

from nutriscan_ai.packages.nutriscan_utils import (
    load_products,
    ProductDB,
    compute_scores_for_product,
)

from nutriscan_ai.vectorstore.build_index import build_index

app = FastAPI(title="NutriScan Copilot", version="0.1.0")


class AskRequest(BaseModel):
    query: str
    barcodes: Optional[List[str]] = None


class AskResponse(BaseModel):
    answer: str
    citations: List[str]


_raw_products = load_products()
_db = ProductDB()
for product in _raw_products:
    scored = compute_scores_for_product(product)
    _db.upsert(scored)

# ---------------------------------------------------------------------------
# Vector store loading
#
# If artefacts created by ``vectorstore/build_index.py`` exist, load them.
# Otherwise build a fresh index from the sample data.  The vector store
# consists of a TF‑IDF vectoriser, the corresponding TF‑IDF matrix, a
# scikit‑learn nearest neighbour index, and a list of barcodes for each
# document.  These are used to provide approximate matches when the
# copilot cannot handle a query via explicit rules.
# ---------------------------------------------------------------------------
_vectoriser = None
_nn_index = None
_matrix = None
_doc_barcodes: List[str] = []


def _ensure_vectorstore() -> None:
    """Load or create the vector store artefacts.

    On the first call this function attempts to load the vectoriser and
    nearest neighbour index from the ``trained_models`` directory.  If the
    files are not present it invokes :func:`build_index` to generate them.
    """
    global _vectoriser, _nn_index, _matrix, _doc_barcodes
    if _vectoriser is not None and _nn_index is not None:
        return
    base_dir = Path(__file__).resolve().parents[2] / "trained_models"
    vectoriser_path = base_dir / "tfidf_vectorizer.joblib"
    nn_path = base_dir / "nearest_neighbors.joblib"
    matrix_path = base_dir / "tfidf_matrix.joblib"
    barcodes_path = base_dir / "doc_barcodes.joblib"
    if vectoriser_path.exists() and nn_path.exists() and matrix_path.exists() and barcodes_path.exists():
        _vectoriser = joblib.load(vectoriser_path)
        _nn_index = joblib.load(nn_path)
        _matrix = joblib.load(matrix_path)
        _doc_barcodes = joblib.load(barcodes_path)
    else:
        # build index and try again
        build_index()
        if vectoriser_path.exists():
            _vectoriser = joblib.load(vectoriser_path)
            _nn_index = joblib.load(nn_path)
            _matrix = joblib.load(matrix_path)
            _doc_barcodes = joblib.load(barcodes_path)
        else:
            # Should not happen unless build_index silently failed
            raise RuntimeError("Failed to build vector store artefacts")


def _all_ingredients_vegan(product: Dict) -> bool:
    for ing in product.get("ingredients", []):
        if not ing.get("vegan_flag", False):
            return False
    return True


def _all_ingredients_vegetarian(product: Dict) -> bool:
    for ing in product.get("ingredients", []):
        if not ing.get("vegetarian_flag", False):
            return False
    return True


def _collect_allergens(product: Dict) -> List[str]:
    allergens = []
    for ing in product.get("ingredients", []):
        allergens.extend(ing.get("allergens_flags", []))
    return list(sorted(set(allergens)))


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    """Answer simple nutrition questions about products.

    The supported question patterns are:

    * "Is this vegan?" or "Is it vegan?" – requires exactly one barcode in
      `barcodes`.  Returns "Yes" if all ingredients have `vegan_flag` true,
      otherwise "No".
    * "Is this vegetarian?" – similar to vegan check but tests
      `vegetarian_flag`.
    * "Compare X and Y" – compare two products.  Requires exactly two
      barcodes.  Returns a sentence comparing sugar, fat and salt content.
    * "Any allergens?" – returns a comma‑separated list of allergens for the
      given barcode.

    For other queries the service apologises and lists the supported actions.
    """
    query = req.query.strip().lower()
    barcodes = req.barcodes or []
    citations: List[str] = []

    if "vegan" in query:
        if len(barcodes) != 1:
            raise HTTPException(status_code=400, detail="Please supply exactly one barcode for a vegan check")
        barcode = barcodes[0]
        product = _db.get(barcode)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        vegan = _all_ingredients_vegan(product)
        answer = "Yes, it is vegan." if vegan else "No, it is not vegan."
        citations = [barcode]
        return AskResponse(answer=answer, citations=citations)

    if "vegetarian" in query:
        if len(barcodes) != 1:
            raise HTTPException(status_code=400, detail="Please supply exactly one barcode for a vegetarian check")
        barcode = barcodes[0]
        product = _db.get(barcode)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        vegetarian = _all_ingredients_vegetarian(product)
        answer = "Yes, it is vegetarian." if vegetarian else "No, it is not vegetarian."
        citations = [barcode]
        return AskResponse(answer=answer, citations=citations)

    if "compare" in query or "difference" in query:
        if len(barcodes) != 2:
            raise HTTPException(status_code=400, detail="Please supply exactly two barcodes for comparison")
        p1 = _db.get(barcodes[0])
        p2 = _db.get(barcodes[1])
        if p1 is None or p2 is None:
            raise HTTPException(status_code=404, detail="One or both products not found")
        # Compare sugar, saturated fat and salt (sodium)
        def fmt_diff(nutrient: str, label: str) -> str:
            v1 = p1["nutrients"].get(nutrient, 0)
            v2 = p2["nutrients"].get(nutrient, 0)
            if v1 < v2:
                return f"{p1['product_name']} has less {label} ({v1} vs {v2} g/100g)"
            elif v1 > v2:
                return f"{p2['product_name']} has less {label} ({v2} vs {v1} g/100g)"
            else:
                return f"Both have the same {label} ({v1} g/100g)"
        parts = [
            fmt_diff("sugars_100g", "sugar"),
            fmt_diff("sat_fat_100g", "saturated fat"),
            fmt_diff("salt_100g", "salt"),
        ]
        answer = "; ".join(parts) + "."
        citations = barcodes
        return AskResponse(answer=answer, citations=citations)

    if "allergen" in query or "allergens" in query:
        if len(barcodes) != 1:
            raise HTTPException(status_code=400, detail="Please supply exactly one barcode to list allergens")
        barcode = barcodes[0]
        product = _db.get(barcode)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        allergens = _collect_allergens(product)
        if allergens:
            answer = "Allergens: " + ", ".join(allergens) + "."
        else:
            answer = "No known allergens."
        citations = [barcode]
        return AskResponse(answer=answer, citations=citations)

    # Default fallback: use vector store to suggest similar products
    _ensure_vectorstore()
    # Compute TF‑IDF vector for the query
    query_vec = _vectoriser.transform([query])
    # Find nearest neighbours (small k ensures quick responses)
    distances, indices = _nn_index.kneighbors(query_vec, n_neighbors=3)
    indices = indices[0]
    recommended_barcodes: List[str] = []
    for idx in indices:
        try:
            recommended_barcodes.append(_doc_barcodes[idx])
        except IndexError:
            continue
    # Build a naive answer listing matching product names
    product_names = []
    for bc in recommended_barcodes:
        prod = _db.get(bc)
        if prod:
            product_names.append(prod.get("product_name", bc))
    if product_names:
        answer = (
            "I'm not sure how to answer that question directly, but here are "
            "some related products: " + ", ".join(product_names) + "."
        )
    else:
        answer = (
            "I'm sorry, I can only answer whether a product is vegan or vegetarian, "
            "compare two products, or list allergens."
        )
    return AskResponse(answer=answer, citations=recommended_barcodes)
