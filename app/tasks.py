from sqlmodel import Session, select
from sqlalchemy import update
from .db import engine
from .models import Wine, LabelTask
import requests, os, logging, json
from openai import OpenAI

BARCODE_KEY = os.getenv("BARCODELOOKUP_KEY")    # set in Render
client = OpenAI(api_key=os.getnenv("OPENAI_API_KEY"))

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

def process_label(task_id: int, image_bytes: bytes, want_review: bool):
    with Session(engine) as s:
        task = s.get(LabelTask, task_id)
        if not task:
            logging.error("Task %s missing", task_id)
            return
        task.status = "processing"
        s.add(task); s.commit()

    # -- OpenAI Vision call here (simplified) --
    response = client.chat.completions.create(
        model="gpt-4o-vision",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "image": image_bytes},
                {"type": "text", "text":
                    "Return JSON keys: producer, label, vintage, region."}
            ]}],
        max_tokens=400,
    )
    data = json.loads(response.choices[0].message.content)

    # Optional quick review
    if want_review:
        review = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a sommelier."},
                {"role": "user",
                 "content": f"Give a 3-sentence overview of {data.get('producer')} {data.get('label')} {data.get('vintage')}."}
            ]).choices[0].message.content
        data["quick_review"] = review
    
    # Save result
    with Session(engine) as s:
        task = s.get(LabelTask, task_id)
        task.status = "done"
        task.payload = data
        s.add(task); s.commit()