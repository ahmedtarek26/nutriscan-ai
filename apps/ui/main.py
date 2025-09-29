"""
Simple Streamlit UI for NutriScan AI.

This module implements a basic, yet functional, Streamlit application for
the NutriScan AI project. It extends the original stub by providing a
barcode lookup form and the ability to retrieve and display Nutri Score
and Eco Score results from the running API service.  Users can enter
a product barcode along with key nutrient values and view the computed
scores in a structured format.  In a fully featured version you would
also include comparison views, charts, and a chat interface backed by
the RAG service.
"""

import streamlit as st
import requests
from typing import Any, Dict
import os

API_BASE = os.getenv("NUTRISCAN_API_BASE", "http://localhost:8000")



def fetch_product(barcode: str, nutrients: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch a product card with scores from the API.

    Args:
        barcode: The product barcode to look up.
        nutrients: A mapping of nutrient field names to numeric values.

    Returns:
        The JSON response from the API as a dictionary. If the request fails,
        returns an empty dict.
    """
    # Build query string from provided nutrient values.
    params = {k: v for k, v in nutrients.items() if v is not None}
    url = f"{API_BASE}/products/{barcode}"
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}


def main() -> None:
    """Render the Streamlit application."""
    st.set_page_config(page_title="NutriScan AI")
    st.title("NutriScan AI")
    st.markdown(
        "Welcome to the NutriScan AI UI. Enter a barcode and nutrient values "
        "below to compute Nutri Score and Eco Score using the local API."
    )

    # Input fields for barcode and nutrients
    barcode = st.text_input("Product barcode", placeholder="e.g. 737628064502")
    col1, col2, col3 = st.columns(3)
    with col1:
        energy = st.number_input("Energy (kcal/100g)", min_value=0.0, value=250.0)
        sugars = st.number_input("Sugars (g/100g)", min_value=0.0, value=15.0)
        sat_fat = st.number_input("Sat. fat (g/100g)", min_value=0.0, value=4.0)
    with col2:
        sodium = st.number_input("Sodium (mg/100g)", min_value=0.0, value=600.0)
        fibre = st.number_input("Fibre (g/100g)", min_value=0.0, value=3.0)
        protein = st.number_input("Protein (g/100g)", min_value=0.0, value=5.0)
    with col3:
        fvnl_percent = st.number_input(
            "Fruit/Veg/Nuts %",
            min_value=0.0,
            max_value=100.0,
            value=30.0,
            help="Percentage of fruit, vegetables, nuts, legumes etc."
        )

    nutrients = {
        "energy_kcal_100g": energy,
        "sugars_100g": sugars,
        "sat_fat_100g": sat_fat,
        "sodium_100g": sodium,
        "fibre_100g": fibre,
        "protein_100g": protein,
        "fvnl_percent": fvnl_percent,
    }

    if st.button("Look up product"):
        if not barcode:
            st.error("Please enter a product barcode.")
        else:
            with st.spinner("Fetching product information..."):
                result = fetch_product(barcode, nutrients)
            if not result:
                st.error(
                    "Could not fetch product. Ensure the API is running on localhost:8000 "
                    "and the barcode/nutrient values are valid."
                )
            else:
                # Display basic product information
                st.subheader("Product details")
                prod_info = {
                    "Barcode": result.get("barcode"),
                    "Name": result.get("product_name"),
                    "Brand": result.get("brand"),
                    "Nutri Score": result.get("nutri_score", {}).get("grade"),
                    "Nutri Score points": result.get("nutri_score", {}).get("score"),
                    "Eco Score": result.get("eco_score", {}).get("grade"),
                    "Eco Score points": result.get("eco_score", {}).get("score"),
                }
                st.table(prod_info.items())
                # Show full JSON as expandable
                with st.expander("Raw API response"):
                    st.json(result)

    # Footer attribution
    st.markdown(
        "---\n"
        "This demo uses the NutriScan API running locally on port 8000. "
        "Make sure to start the API service before using this UI."
    )

if __name__ == "__main__":
    main()
