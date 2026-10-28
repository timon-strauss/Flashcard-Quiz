# Flashcards

A browser-based flashcard app — FastAPI backend, React frontend, SQLite storage.

## Project structure

```
flashcards/
├── backend/        # FastAPI app (uvicorn)
├── frontend/       # React app (Vite)
├── mcp-server/     # Read-only MCP server (talks to backend API only)
├── data/           # SQLite database file (created at runtime)
└── Dockerfile      # Single image: frontend + backend + MCP behind nginx
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

### MCP-Server

Read-only MCP-Server, der ausschließlich über die HTTP-API mit dem Backend spricht (keine DB- oder Dateizugriffe, nur GET-Requests).

```bash
cd mcp-server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

Läuft auf **http://localhost:8001/mcp** (Streamable HTTP) und erwartet das Backend unter `http://localhost:8000`.

Konfiguration per Umgebungsvariablen:

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `BACKEND_URL` | `http://localhost:8000` | URL des Backends |
| `MCP_HOST` | `127.0.0.1` | Bind-Adresse |
| `MCP_PORT` | `8001` | Port |
| `MCP_TRANSPORT` | `streamable-http` | `streamable-http`, `sse` oder `stdio` |

Tools: `list_topics`, `get_topic`, `list_topic_decks`, `list_decks`, `get_deck`, `list_deck_cards`, `get_card`, `get_card_image`, `get_all_content`.

In Claude Code einbinden:

```bash
claude mcp add --transport http flashcards http://localhost:8001/mcp        # lokal
claude mcp add --transport http flashcards http://localhost:3000/mcp        # Podman-Container
```

### Alles zusammen starten (lokal)

Öffne drei Terminals und führe folgendes aus:

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

**Terminal 3 — MCP-Server (optional):**
```bash
source mcp-server/.venv/bin/activate
cd mcp-server && python server.py
```

Dann im Browser öffnen: **http://localhost:5173**

## Production (Podman)

### First run

```bash
cd ~/Desktop/flashcards
podman build -t flashcards .
podman run -d \
  -p 3000:80 \
  -v flashcards-data:/app/data \
  -v flashcards-uploads:/app/uploads \
  --name flashcards \
  flashcards
```

App runs at **http://localhost:3000**. Other devices on the same network can reach it at `http://<your-ip>:3000`.

Everything runs in one container behind nginx on port 80 (mapped to 3000):

| Path | Routed to |
|------|-----------|
| `/` | Frontend (static build) |
| `/api/`, `/uploads/` | Backend (`127.0.0.1:8000`) |
| `/mcp` | MCP server (`127.0.0.1:8001`) |

Data is stored in Podman-managed named volumes (`flashcards-data`, `flashcards-uploads`) — not in your project folder. It persists across container restarts and rebuilds.

### Update after code changes

```bash
podman stop flashcards
podman rm flashcards
podman build -t flashcards .
podman run -d \
  -p 3000:80 \
  -v flashcards-data:/app/data \
  -v flashcards-uploads:/app/uploads \
  --name flashcards \
  flashcards
```

The volumes are reattached automatically — no data is lost.

### Stop / start

```bash
podman stop flashcards   # stop
podman start flashcards  # start again (no rebuild needed)
```

### Manage volumes

```bash
podman volume ls                        # list volumes
podman volume inspect flashcards-data   # see details
podman volume rm flashcards-data        # delete volume (loses data!)
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
