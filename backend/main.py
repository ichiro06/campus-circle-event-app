from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine, get_db
from models import CampusEvent, Circle
from schemas import CircleRead, EventRead
from seed import seed_database

DatabaseSession = Annotated[Session, Depends(get_db)]


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_database(session)
    yield


app = FastAPI(title="Campus Circle API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Campus Circle API is ready"}


@app.get("/health")
def health_check(db: DatabaseSession):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(status_code=503, detail="Database is unavailable") from error
    return {"status": "ok", "database": "connected"}


@app.get("/api/circles", response_model=list[CircleRead])
def list_circles(db: DatabaseSession):
    return db.scalars(select(Circle).order_by(Circle.id)).all()


@app.get("/api/events", response_model=list[EventRead])
def list_events(db: DatabaseSession):
    return db.scalars(select(CampusEvent).order_by(CampusEvent.starts_at)).all()
