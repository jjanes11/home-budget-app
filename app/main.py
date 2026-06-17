from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models  # noqa: F401 – registers all models with Base.metadata
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Home Budget API", lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"status": "ok"}
