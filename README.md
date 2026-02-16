# Checkers Game

A modern online Checkers game built with **FastAPI** (Python) and **React** (Vite + TypeScript).

## Features
- **Multiplayer:** Play against friends by sharing a Game ID.
- **Backend:** FastAPI with SQLAlchemy and PostgreSQL.
- **Frontend:** React with Tailwind CSS.
- **Game Logic:** Standard checkers rules (movement, captures, king promotion).
- **Architecture:** REST API with polling for game state updates.

## Prerequisites
- Node.js (v18+)
- Python (v3.10+)
- PostgreSQL (or Docker)

## Setup & Run

### 1. Database Setup
Ensure PostgreSQL is running and create the database. The easiest way is via Docker:
```bash
docker-compose up -d
```
This runs Postgres on port `5433` (to avoid local conflicts).

### 2. Backend
Navigate to the `be` directory:
```bash
cd be
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
The API will run at `http://localhost:8000`.

### 3. Frontend
Navigate to the `fe` directory:
```bash
cd fe
npm install
npm run dev
```
The game will run at `http://localhost:5173`.

## Gameplay
1. Open the frontend in your browser.
2. **Player 1:** Click **"Create New Game"**. You are assigned **Red**.
3. Share the **Game ID** (displayed at the top) with a friend.
4. **Player 2:** Open the game on another device/tab, enter the Game ID, and click **"Join"**. You are assigned **Black**.
5. The game syncs automatically. Turns are enforced (you can only move your own pieces).
