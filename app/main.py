# app/main.py
from fastapi import FastAPI, Depends
from sqlmodel import Session, select
from .db import init_db, get_session
from .models import Wine

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