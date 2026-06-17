from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models  # noqa: F401 – registers all models with Base.metadata
from app.api.routers import auth as auth_router
from app.api.routers import categories as categories_router
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Home Budget API", lifespan=lifespan)

app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
app.include_router(categories_router.router, prefix="/categories", tags=["categories"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
