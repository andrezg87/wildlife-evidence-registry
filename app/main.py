from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.connection import connect_to_database, disconnect_from_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_database()
    yield
    await disconnect_from_database()


app = FastAPI(title="Wildlife Evidence Registry", lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"status": "ok"}
