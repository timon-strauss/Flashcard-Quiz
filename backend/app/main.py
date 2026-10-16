import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import DatabaseAPI

app = FastAPI(title="Flashcards API")

_raw_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173",
)
origins = [o.strip() for o in _raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    DatabaseAPI.start_db()



@app.get("/health")
def health():
    return {"status": "ok"}
