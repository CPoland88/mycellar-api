from sqlmodel import Session, select
from sqlalchemy import update
from .db import engine
from .models import Wine
import requests, os, logging

BARCODE_KEY = os.getenv("BARCODELOOKUP_KEY")    # set in Render later

def enrich_from_barcode(wine_id: int, barcode: str) -> None:
    """Fetch producer/label via BarcodeLookup and update the Wine row."""
    
    # skip gracefully if API key is missing
    if not BARCODE_KEY:
        logging.warning("BARCODELOOKUP_KEY not set; skipping enrichment")
        return
    
    # call the external REST API
    url = (
        "https://api.barcodelookup.com/v3/products"
        f"?barcode={barcode}&key={BARCODE_KEY}"
    )
    try:
        product = requests.get(url, timeout=10).json()["products"][0]
    except Exception as exc:
        logging.error("Lookup failed for %s: %s", barcode, exc)
        return
    
    # patch the Wine row inside its own session/transaction
    with Session(engine) as s:
        wine = s.exec(select(Wine).where(Wine.id == wine_id)).one()
        wine.producer = product.get("brand") or wine.producer
        wine.label = product.get("product_name") or wine.label
        s.add(wine)
        s.commit()