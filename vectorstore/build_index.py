"""Utilities for building a simple vector store for NutriScan AI.

The production‑grade design for NutriScan AI calls for a retrieval‑augmented
generation (RAG) pipeline built on top of a high‑quality embedding model and
a nearest‑neighbour index (e.g., FAISS).  However, this development
environment does not have access to large transformer models or the ability
to install additional dependencies.  To provide a working proof of concept
that exercises the same interfaces, this module implements a very basic
vector store using scikit‑learn's ``TfidfVectorizer`` and ``NearestNeighbors``.

The ``build_index`` function reads the normalised product data from the
``data`` directory, constructs simple text documents for each product, fits
a TF‑IDF vectoriser, and then trains a nearest neighbour model.  The
resulting vectoriser, matrix and index are persisted to the ``trained_models``
directory.  These artefacts can later be loaded by the RAG service to
perform approximate document retrieval.  A list of barcodes corresponding
to each document is also saved so that retrieved indices can be mapped back
to products.

This implementation should be viewed as a placeholder for a more
sophisticated RAG pipeline.  When internet access and GPU resources are
available you can replace the TF‑IDF vectoriser with a pretrained
transformer (e.g., sentence‑transformers) and swap ``NearestNeighbors`` for
a FAISS index.  The high‑level API (``vectorise`` and ``search``) can
remain unchanged.
"""

import json
import os
from pathlib import Path
from typing import List, Dict

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors


def _load_products() -> List[Dict]:
    """Load sample products from the ``data`` directory.

    The current project ships with a small JSON dataset located at
    ``nutriscan_ai/data/sample_products.json``.  Each element contains
    keys such as ``barcode``, ``product_name``, ``ingredients``,
    ``nutrients`` (a mapping of nutrient names to values), and flags like
    ``vegan_flag`` or ``allergens_flags``.  If you extend the project to
    ingest the nightly Open Food Facts dump, you can reuse this function
    to load a much larger dataset.

    Returns:
        A list of product dictionaries.
    """
    data_path = Path(__file__).resolve().parent.parent / "data" / "sample_products.json"
    if not data_path.exists():
        raise FileNotFoundError(f"Sample data not found at {data_path}")
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_documents(products: List[Dict]) -> List[str]:
    """Construct a free‑text document for each product.

    To compute TF‑IDF features we need a string for each product that
    concisely represents its content.  This function concatenates the
    product name, list of ingredients, nutrient key/value pairs and
    computed score letters into a single string.  You can experiment with
    different templates here to improve retrieval performance.

    Args:
        products: List of product dictionaries.

    Returns:
        List of strings representing each product.
    """
    documents = []
    for prod in products:
        parts = []
        # Basic identifiers
        parts.append(prod.get("product_name", ""))
        parts.append(prod.get("brand", ""))
        # Ingredients
        ingredients = prod.get("ingredients", [])
        if isinstance(ingredients, list):
            parts.extend(ingredients)
        elif isinstance(ingredients, str):
            parts.append(ingredients)
        # Nutrients
        nutrients: Dict[str, float] = prod.get("nutrients", {})
        for k, v in nutrients.items():
            parts.append(f"{k} {v}")
        # Labels
        labels = prod.get("labels", [])
        if isinstance(labels, list):
            parts.extend(labels)
        # Scores
        if (letter := prod.get("nutri_score", None)):
            parts.append(f"NutriScore {letter}")
        if (eco := prod.get("eco_score", None)):
            parts.append(f"EcoScore {eco}")
        documents.append(" ".join(str(p) for p in parts if p))
    return documents


def build_index() -> None:
    """Build and persist the TF‑IDF vectoriser and nearest neighbour index.

    This function performs the end‑to‑end workflow: load product data,
    construct documents, fit the vectoriser, compute the TF‑IDF matrix,
    train the nearest neighbour model, and save all artefacts.  It also
    writes out the list of barcodes corresponding to each document so that
    the index can be mapped back to product records.
    """
    products = _load_products()
    if not products:
        raise RuntimeError("No products found to index.")
    documents = _build_documents(products)

    # Fit TF‑IDF vectoriser
    vectoriser = TfidfVectorizer(stop_words="english")
    matrix = vectoriser.fit_transform(documents)

    # Train nearest neighbour index using cosine distance
    nn = NearestNeighbors(metric="cosine", n_neighbors=5)
    nn.fit(matrix)

    # Prepare output directory
    out_dir = Path(__file__).resolve().parent.parent / "trained_models"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Persist artefacts
    joblib.dump(vectoriser, out_dir / "tfidf_vectorizer.joblib")
    joblib.dump(nn, out_dir / "nearest_neighbors.joblib")
    joblib.dump(matrix, out_dir / "tfidf_matrix.joblib")
    joblib.dump([prod.get("barcode") for prod in products], out_dir / "doc_barcodes.joblib")

    print(f"Vector store built. Stored artefacts in {out_dir}")


if __name__ == "__main__":
    build_index()
