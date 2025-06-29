from sqlmodel import SQLModel, create_engine, Session
import os

# Pick engine based on env-var: Postgres in prod, SQLite in dev
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cellar.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

def init_db() -> None:
    from . import models    # noqa: F401 - makes sure models are imported
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session       # FastAPI dependency pattern