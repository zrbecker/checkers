import time
from collections import defaultdict
from typing import Dict, Tuple

class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_update = time.time()

    def consume(self, tokens: int = 1) -> bool:
        now = time.time()
        time_passed = now - self.last_update
        self.last_update = now
        
        # Refill
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

class RateLimiter:
    """
    In-memory rate limiter using Token Bucket algorithm.
    
    Note: Since this stores state in memory, limits are per-process (per-worker).
    If running with multiple Uvicorn workers, the effective global limit will be
    (limit * number_of_workers). For strictly global limits across workers,
    an external store like Redis would be required.
    """
    def __init__(self):
        # Global buckets
        self.global_game_create = TokenBucket(capacity=10, refill_rate=10.0)
        self.global_move = TokenBucket(capacity=100, refill_rate=100.0)
        self.global_query = TokenBucket(capacity=1000, refill_rate=1000.0)
        
        # Session buckets: ip -> bucket
        # Storing last access to potentially clean up, but keeping it simple for now
        self.session_game_create: Dict[str, TokenBucket] = defaultdict(lambda: TokenBucket(capacity=1, refill_rate=1.0))
        self.session_move: Dict[str, TokenBucket] = defaultdict(lambda: TokenBucket(capacity=1, refill_rate=1.0))
        self.session_query: Dict[str, TokenBucket] = defaultdict(lambda: TokenBucket(capacity=10, refill_rate=10.0))

    def check_game_create(self, session_id: str) -> bool:
        # Check global first
        if not self.global_game_create.consume():
            return False
        # Check session
        if not self.session_game_create[session_id].consume():
            return False
        return True

    def check_move(self, session_id: str) -> bool:
        if not self.global_move.consume():
            return False
        if not self.session_move[session_id].consume():
            return False
        return True

    def check_query(self, session_id: str) -> bool:
        if not self.global_query.consume():
            return False
        if not self.session_query[session_id].consume():
            return False
        return True

# Singleton instance
limiter = RateLimiter()
