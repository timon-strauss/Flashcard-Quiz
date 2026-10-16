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
npm install
npm run dev
```

Runs on **http://localhost:5173**. API calls are automatically proxied to the backend via Vite's dev proxy — no CORS issues, no configuration needed.

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
