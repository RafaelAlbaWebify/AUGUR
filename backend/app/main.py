from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.db.bootstrap import initialize_datastores


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_datastores()
    yield


app = FastAPI(
    title="AUGUR API",
    version="0.1.0-phase1",
    description="Local-first country trajectory and personal fit engine.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5190",
        "http://localhost:5190",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "AUGUR",
        "version": "0.1.0-phase1",
        "status": "running",
        "docs": "/docs",
    }
