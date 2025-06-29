from app.db import init_db, engine
from app.models import Wine
from sqlmodel import Session, select

# 1) Ensure tables exist
init_db()

# 2) Insert a test wine and query it back
with Session(engine) as s:
    s.add(Wine(producer="Dominus", vintage=2018))
    s.commit()

    # Fetch all wines
    wines = s.exec(select(Wine)).all()
    print(wines)