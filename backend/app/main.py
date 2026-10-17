import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import db as DatabaseAPI
from .routers import topics, decks, cards

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "Upload")
os.makedirs(UPLOAD_DIR, exist_ok=True)

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


app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(topics.router)
app.include_router(decks.router)
app.include_router(cards.router)



@app.get("/health")
def health():
    return {"status": "ok"}
