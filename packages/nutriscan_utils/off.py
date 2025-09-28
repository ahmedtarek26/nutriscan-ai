"""
Client for interacting with the Open Food Facts API.
"""

import requests

BASE_URL = "https://world.openfoodfacts.org/api/v0/product"

def fetch_product(barcode: str) -> dict:
    """
    Fetch product information from Open Food Facts API by barcode.
    Returns parsed JSON as a dictionary.
    """
    response = requests.get(f"{BASE_URL}/{barcode}.json")
    response.raise_for_status()
    return response.json()
