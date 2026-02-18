import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.future import select
from sqlalchemy import func

from database import engine, Base
from models import Game
from telemetry import setup_telemetry, setup_db_telemetry, GAMES_ACTIVE
from routers.games import router as games_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Suppress uvicorn access logs (200 OKs), keep errors
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Initialize active games count
    async with engine.connect() as conn:
        stmt = select(func.count(Game.id)).where(Game.status == "active")
        result = await conn.execute(stmt)
        active_count = result.scalar() or 0
        GAMES_ACTIVE.set(active_count)
    
    yield

app = FastAPI(title="Checkers API", lifespan=lifespan)

# Setup Telemetry
setup_telemetry(app)
setup_db_telemetry(engine)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "*"], # Allow Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games_router)

# Serve Frontend
frontend_dist = os.getenv("FRONTEND_DIST")
if frontend_dist and os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Check if file exists in dist (e.g. favicon.ico, etc)
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # Otherwise return index.html
        return FileResponse(os.path.join(frontend_dist, "index.html"))
