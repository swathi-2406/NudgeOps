"""
Simple in-memory rate limiter.
Uses a sliding window counter per IP address.
Production: swap with Redis-backed rate limiting.
"""
import time
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """Sliding window rate limiter — stored in memory."""

    def __init__(self):
        # {ip: [(timestamp, endpoint)]}
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, ip: str, window_seconds: int, max_requests: int) -> bool:
        now = time.time()
        cutoff = now - window_seconds

        # Clean old entries
        self._requests[ip] = [t for t in self._requests[ip] if t > cutoff]

        if len(self._requests[ip]) >= max_requests:
            return False

        self._requests[ip].append(now)
        return True


# Global limiter instance
_limiter = RateLimiter()

# Route-specific limits: (max_requests, window_seconds)
ROUTE_LIMITS = {
    "/api/v1/habitflow/auth/signup": (10, 3600),   # 10 signups/hour per IP
    "/api/v1/habitflow/auth/login":  (20, 3600),   # 20 logins/hour per IP
    "/api/v1/habitflow/nudge/request": (50, 3600), # 50 nudges/hour per IP
    "/api/v1/events/":               (200, 3600),  # 200 events/hour per IP
    "/api/v1/events/batch":          (50, 3600),   # 50 batch/hour per IP
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Check if this route has a limit
        for route, (max_req, window) in ROUTE_LIMITS.items():
            if path.startswith(route):
                key = f"{ip}:{route}"
                if not _limiter.is_allowed(key, window, max_req):
                    raise HTTPException(
                        status_code=429,
                        detail=f"Too many requests. Try again later."
                    )
                break

        return await call_next(request)
