from sqlmodel import Field, SQLModel, Relationship
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, JSON

class Wine(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    producer: str | None = None
    label: str | None = None
    vintage: int | None = None
    region: str | None = None
    country: str | None = None
    upc: str | None = Field(default=None, index=True, unique=True)
    critic_data: dict | None = Field(default=None, sa_column=Column(JSON))
    drink_from: date | None = None
    drink_to: date | None = None

    bottles: List["Bottle"] = Relationship(back_populates="wine")
    
class Bottle(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    wine_id: int = Field(foreign_key="wine.id")
    purchase_price: float | None = None
    slot: str | None = Field(unique=True)
    
    wine: Wine = Relationship(back_populates="bottles")

class LabelTask(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: str = "queued"          # queued -> processing -> done/failed)
    payload: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)