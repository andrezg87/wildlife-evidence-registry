from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.connection import connect_to_database, disconnect_from_database
from app.presentation import (
    auth_router,
    case_router,
    evidence_router,
    species_router,
    suspect_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_database()
    yield
    await disconnect_from_database()


app = FastAPI(title="Wildlife Evidence Registry", lifespan=lifespan)

app.include_router(species_router.router)
app.include_router(auth_router.router)
app.include_router(case_router.router)
app.include_router(evidence_router.router)
app.include_router(suspect_router.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
