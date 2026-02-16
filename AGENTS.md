# Checkers Game - Agent Context

This file provides context for AI agents working on this repository.

## 1. Project Overview
This is a multiplayer online Checkers game.
- **Goal:** Allow two players to play checkers in real-time (or near real-time via polling/updates).
- **Core Mechanics:** Standard checkers rules, including mandatory captures, double jumps, and king promotion.
- **State:** Game state is persisted in a PostgreSQL database.

## 2. Tech Stack

### Backend (`be/`)
- **Language:** Python 3.10+
- **Framework:** FastAPI
- **Database ORM:** SQLAlchemy (Async)
- **Database Driver:** asyncpg
- **Server:** Uvicorn
- **Dependency Management:** `requirements.txt` / `venv`

### Frontend (`fe/`)
- **Language:** TypeScript
- **Framework:** React
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **State Management:** React Context or local state (verify in code)
- **Communication:** REST API (JSON)

### Infrastructure
- **Database:** PostgreSQL (v15-alpine)
- **Containerization:** Docker Compose (`docker-compose.yml`)

## 3. Architecture & Directory Structure

```
/
├── be/                 # Backend (FastAPI)
│   ├── main.py         # API Entrypoint & Routes
│   ├── logic.py        # Core Checkers Game Logic (Pure Python)
│   ├── models.py       # SQLAlchemy Database Models
│   ├── schemas.py      # Pydantic Schemas (API Request/Response)
│   ├── database.py     # DB Connection & Session Management
│   └── venv/           # Python Virtual Environment
├── fe/                 # Frontend (React + Vite)
│   ├── src/            # Source code
│   ├── public/         # Static assets
│   └── package.json    # Frontend dependencies
├── docker-compose.yml  # Database orchestration
└── README.md           # Human-readable documentation
```

## 4. Development Workflow

### Starting the Project
1.  **Database:** `docker-compose up -d db` (Runs Postgres on port 5433)
2.  **Backend:**
    ```bash
    cd be
    source venv/bin/activate
    uvicorn main:app --reload
    ```
3.  **Frontend:**
    ```bash
    cd fe
    npm run dev
    ```

### Testing
- **Backend Tests:** Run `pytest` in `be/` (if tests exist).
- **Frontend Tests:** Run `npm test` in `fe/`.

## 5. Coding Conventions

### Python (Backend)
- **Type Hints:** MANDATORY. Use `typing.List`, `typing.Optional`, etc. or standard types in 3.10+.
- **Async:** Use `async def` for all route handlers and DB operations.
- **Pydantic:** Use Pydantic models for all request bodies and response schemas.
- **SQLAlchemy:** Use 2.0 style (`select(Model).where(...)`) and async sessions.

### TypeScript (Frontend)
- **Strict Mode:** TypeScript strict mode is likely enabled. Avoid `any`.
- **Components:** Functional components with Hooks.
- **Styling:** Use Utility classes (Tailwind) over CSS files where possible.

## 6. Key Implementation Details
- **Game Logic:** The `be/logic.py` file contains the "source of truth" for valid moves. Do not duplicate validation logic in the frontend if possible; trust the backend validation.
- **State Sync:** The frontend polls or requests game state. The `GameState` schema in `be/schemas.py` defines the wire format.
- **Turn Management:** The backend enforces turns (`current_turn` field).

## 7. Common Tasks for Agents
- **Refactoring:** When refactoring `logic.py`, ensure unit tests (if any) are updated.
- **Adding Features:** If adding a feature (e.g., chat, spectator mode), add the Model first, then Schema, then API endpoint, then Frontend UI.
- **Debugging:** Check `docker-compose logs db` for DB issues and Uvicorn logs for API errors.
