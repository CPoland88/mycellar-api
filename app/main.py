# app/main.py
from fastapi import FastAPI

app = FastAPI(title="CellarCore")

@app.get("/")
def root():
    """Simple health-check endpoint."""
    return {"hello": "world"}
