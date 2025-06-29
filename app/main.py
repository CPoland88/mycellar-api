# app/main.py
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from sqlmodel import Session, select
from dotenv import load_dotenv
from typing import List
from .db import init_db, get_session
from .models import Wine, Bottle
from .schemas import ScanIn
from .tasks import enrich_from_barcode

# Load environment variables from .env file
load_dotenv()

# existing FastAPI instance:
app = FastAPI(title="CellarCore")

@app.on_event("startup")
def on_startup():
    init_db()           # creates tables if they don't exist

@app.get("/")
def health():
    return {"ok": True}

# simple GET -> list wines
@app.get("/wines/{wine_id}", response_model=Wine)
def get_wine_with_bottles(
    wine_id: int,
    db: Session = Depends(get_session)
):
    wine = db.exec(select(Wine).where(Wine.id == wine_id)).first()
    if wine is None:
        raise HTTPException(404, f"Wine {wine_id} not found")
    # trigger lazy load of related bottles
    _ = wine.bottles
    return wine

@app.post("/scan", status_code=202)
def add_bottle(
    scan: ScanIn,
    bg: BackgroundTasks,
    db: Session = Depends(get_session)
):
    barcode_str = str(scan.barcode)     # ensure barcode is a string

    # 1. find or create the Wine row (by barcode)
    wine = db.exec(select(Wine).where(Wine.upc == barcode_str)).first()
    is_new = False
    if wine is None:
        wine = Wine(upc=barcode_str)   # placeholder, enrich later
        db.add(wine)
        is_new = True
        db.flush()                      # assigns wine.id

    # 2. prevent slot conflicts (if a slot was provided)
    if scan.slot:
        exists = db.exec(select(Bottle).where(Bottle.slot == scan.slot)).first()
        if exists:
            raise HTTPException(409, f"Slot {scan.slot} already occupied")
        
    # 3. create the Bottle row
    bottle = Bottle(
        wine_id = wine.id,
        purchase_price = scan.price,
        slot = scan.slot
    )
    db.add(bottle)
    db.commit()

    #4. one-time enrichment for new barcodes
    if is_new:
        bg.add_task(enrich_from_barcode, wine.id, barcode_str)
        
    return {
        "wine_id": wine.id,
        "bottle_id": bottle.id,
        "queued_enrichment": is_new
    }

@app.delete("/wines/{wine_id}", status_code=204)
def delete_wine(
    wine_id: int,
    db: Session = Depends(get_session)
):
    wine = db.get(Wine, wine_id)
    if wine is None:
        raise HTTPException(404, f"Wine {wine_id} not found")
    
    # delete all bottles tied to this wine
    for b in wine.bottles:
        db.delete(b)

    # now delete the wine itself
    db.delete(wine)
    db.commit()