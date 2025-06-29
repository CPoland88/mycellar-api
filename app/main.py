# app/main.py
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from sqlmodel import Session, select
from .db import init_db, get_session
from .models import Wine, Bottle
from .schemas import ScanIn
from .tasks import enrich_from_barcode

# existing FastAPI instance:
app = FastAPI(title="CellarCore")

@app.on_event("startup")
def on_startup():
    init_db()           # creates tables if they don't exist

@app.get("/")
def health():
    return {"ok": True}

# simple GET -> list wines
@app.get("/wines")
def list_wines(session: Session = Depends(get_session)):
    return session.exec(select(Wine)).all()

@app.post("/scan", status_code=202)
def add_bottle(
    scan: ScanIn,
    bg: BackgroundTasks,
    db: Session = Depends(get_session)
):
    # 1. find or create the Wine row (by barcode)
    wine = db.exec(select(Wine).where(Wine.upc == scan.barcode)).first()
    is_new = False
    if wine is None:
        wine = Wine(upc=scan.barcode)   # placeholder, enrich later
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
        bg.add_task(enrich_from_barcode, wine.id, scan.barcode)
        
    return {
        "wine_id": wine.id,
        "bottle_id": bottle.id,
        "queued_enrichment": is_new
    }