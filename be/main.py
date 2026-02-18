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
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    origins = allowed_origins_env.split(",")
else:
    # Default for local development
    origins = ["http://localhost:5173", "http://localhost:5174"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "HEAD"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

app.include_router(games_router)

# Serve Frontend
frontend_dist = os.getenv("FRONTEND_DIST")
if frontend_dist and os.path.isdir(frontend_dist):
    frontend_dist_str = frontend_dist
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Check if file exists in dist (e.g. favicon.ico, etc)
        file_path = os.path.join(frontend_dist_str, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # Otherwise return index.html
        return FileResponse(os.path.join(frontend_dist_str, "index.html"))
