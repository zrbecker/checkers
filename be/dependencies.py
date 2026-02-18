from fastapi import Request, HTTPException, status
from rate_limiter import limiter

async def check_create_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    if not limiter.check_game_create(ip):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded. Try again later.")

async def check_move_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    if not limiter.check_move(ip):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded. Try again later.")

async def check_query_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    if not limiter.check_query(ip):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded. Try again later.")
