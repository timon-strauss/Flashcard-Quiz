# Flashcards

A browser-based flashcard app — FastAPI backend, React frontend, SQLite storage.

## Project structure

```
flashcards/
├── backend/        # FastAPI app (uvicorn)
├── frontend/       # React app (Vite)
├── data/           # SQLite database file (created at runtime)
└── docker-compose.yml
```

## Development (local)

Run backend and frontend in separate terminals.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The venv only needs to be created once. On subsequent runs just activate it:

```bash
source backend/.venv/bin/activate
cd backend && uvicorn app.main:app --reload
```

Runs on **http://localhost:8000**. Interactive API docs available at http://localhost:8000/docs.

### Frontend

```bash
cd frontend
npm install        # only needed once
npm run dev
```

Runs on **http://localhost:5173**. API calls are automatically proxied to the backend via Vite's dev proxy — no CORS configuration needed.

> **Hinweis:** Das Frontend erwartet, dass das Backend unter `http://localhost:8000` läuft. Starte das Backend zuerst, bevor du das Frontend öffnest.

### Alles zusammen starten (lokal)

Öffne zwei Terminals und führe folgendes aus:

**Terminal 1 — Backend:**
```bash
source backend/.venv/bin/activate
cd backend && uvicorn app.main:app --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm install        # nur beim ersten Mal nötig
npm run dev
```

Dann im Browser öffnen: **http://localhost:5173**

## Production (Docker)

```bash
docker-compose up --build
```

- Frontend: **http://localhost:3000**
- Backend: **http://localhost:8000**

The SQLite database is stored in `./data/flashcards.db` on the host and persists across container restarts. To stop without removing data:

```bash
docker-compose down
```

## Testing

Unit tests cover the database layer (Topics, Decks, Cards CRUD). They run against an in-memory SQLite database — no files are created on disk.

```bash
cd backend
source .venv/bin/activate   # activate venv if not already active
pytest tests/
```

Run with verbose output to see each test name:

```bash
pytest tests/ -v
```

Run a single module:

```bash
pytest tests/test_topics.py
pytest tests/test_decks.py
pytest tests/test_cards.py
```

### Test layout

```
backend/
└── tests/
    ├── conftest.py       # shared api fixture (in-memory DB)
    ├── test_topics.py    # Topic CRUD + cascade delete
    ├── test_decks.py     # Deck CRUD + topic association + cascade delete
    └── test_cards.py     # Card CRUD + filtering by deck/topic
```

## API overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/decks` | List all decks |
| POST | `/decks` | Create a deck |
| GET | `/decks/{id}` | Get a deck |
| PUT | `/decks/{id}` | Update a deck |
| DELETE | `/decks/{id}` | Delete a deck (and its cards) |
| GET | `/decks/{id}/cards` | List cards in a deck |
| POST | `/decks/{id}/cards` | Add a card to a deck |
| GET | `/cards/{id}` | Get a card |
| PUT | `/cards/{id}` | Update a card |
| DELETE | `/cards/{id}` | Delete a card |
