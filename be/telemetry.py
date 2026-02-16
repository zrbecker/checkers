from prometheus_client import Counter, Histogram, Gauge
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from fastapi import FastAPI, Request
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine
import time

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

# --- Custom HTTP Metrics ---
HTTP_REQUEST_SIZE = Histogram(
    "http_request_size_bytes",
    "Content-Length of HTTP requests",
    buckets=[100, 500, 1000, 5000, 10000, 50000, 100000]
)

HTTP_RESPONSE_SIZE = Histogram(
    "http_response_size_bytes",
    "Content-Length of HTTP responses",
    buckets=[100, 500, 1000, 5000, 10000, 50000, 100000]
)

CONCURRENT_REQUESTS = Gauge(
    "http_concurrent_requests",
    "Number of concurrent HTTP requests"
)

def setup_telemetry(app: FastAPI):
    # Initialize Instrumentator
    # We exclude /metrics from metrics to avoid pollution
    instrumentator = Instrumentator(
        excluded_handlers=["/metrics"],
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_instrument_requests_inprogress=True,
    )
    
    # Add default metrics (latency, requests, etc.)
    instrumentator.instrument(app)
    
    # Expose /metrics
    instrumentator.expose(app)
    
    # Add concurrent requests middleware
    @app.middleware("http")
    async def track_concurrency(request: Request, call_next):
        CONCURRENT_REQUESTS.inc()
        try:
            # Track request size
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    HTTP_REQUEST_SIZE.observe(float(content_length))
                except ValueError:
                    pass
            
            response = await call_next(request)
            
            # Track response size
            response_content_length = response.headers.get("content-length")
            if response_content_length:
                 try:
                    HTTP_RESPONSE_SIZE.observe(float(response_content_length))
                 except ValueError:
                    pass
            
            return response
        finally:
            CONCURRENT_REQUESTS.dec()

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
