from prometheus_client import Counter, Histogram, Gauge, start_http_server
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from fastapi import FastAPI
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine
import time
import os

# --- Business Metrics ---
GAMES_CREATED = Counter(
    "checkers_games_created_total",
    "Total number of games created"
)

GAMES_ACTIVE = Gauge(
    "checkers_games_active",
    "Number of currently active games"
)

MOVES_MADE = Counter(
    "checkers_moves_total",
    "Total number of moves made"
)

# --- DB Metrics ---
DB_QUERIES = Counter(
    "checkers_db_queries_total",
    "Total number of database queries executed"
)

DB_LATENCY = Histogram(
    "checkers_db_query_duration_seconds",
    "Database query latency",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.5, 1.0, 5.0]
)

def setup_telemetry(app: FastAPI):
    # Initialize Instrumentator
    # We DO NOT use expose(app) anymore as we want a separate port
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_instrument_requests_inprogress=True,
    )
    
    # Add default metrics (latency, requests, etc.)
    instrumentator.add(metrics.default())
    instrumentator.instrument(app)
    
    # Start Prometheus Metrics Server on separate port (9091 by default)
    # This runs in a background thread
    metrics_port = int(os.getenv("METRICS_PORT", "9091"))
    try:
        start_http_server(metrics_port)
        print(f"Metrics server started on port {metrics_port}")
    except Exception as e:
        print(f"Failed to start metrics server on port {metrics_port}: {e}")

def setup_db_telemetry(engine):
    # If using async engine, event listeners must attach to the sync_engine
    target = engine.sync_engine if isinstance(engine, AsyncEngine) else engine

    @event.listens_for(target, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        context._query_start_time = time.time()

    @event.listens_for(target, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - context._query_start_time
        DB_QUERIES.inc()
        DB_LATENCY.observe(total)
