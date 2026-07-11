"""
Tracing, structured logging context, and sliding-window rate limiting middlewares
for the Nexus AI Operations Platform.
"""

import time
import uuid
import sys
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logger import logger, request_id_ctx, mission_id_ctx
from app.core.config import settings


class TracingAndLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that establishes Request ID and Mission ID thread-safe context traces,
    measuring latency, and outputting structured JSON logging variables.
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        
        # 1. Resolve X-Request-ID from headers or generate brand-new UUID tracking ID
        req_id = request.headers.get("X-Request-ID")
        if not req_id:
            req_id = str(uuid.uuid4())
            
        # 2. Resolve Mission ID context
        mission_id = request.headers.get("X-Mission-ID")
        if not mission_id:
            mission_id = request.query_params.get("mission_id")
        if not mission_id:
            # Parse from URI structure claims/RUN-XXXX/something
            path_parts = request.url.path.strip("/").split("/")
            if len(path_parts) >= 2 and path_parts[0] == "claims":
                mission_id = path_parts[1]
                
        # 3. Store tracking variables in thread-local storage context vars
        request_id_token = request_id_ctx.set(req_id)
        mission_id_token = mission_id_ctx.set(mission_id)
        
        try:
            response = await call_next(request)
            
            duration = time.perf_counter() - start_time
            # Standardized operational log trace
            logger.info(
                f"[HTTP] {request.method} {request.url.path} finished with status={response.status_code} in {duration:.4f}s",
                extra={
                    "extra_fields": {
                        "request_id": req_id,
                        "mission_id": mission_id,
                        "duration_sec": duration,
                        "status_code": response.status_code,
                        "method": request.method,
                        "path": request.url.path
                    }
                }
            )
            
            # Expose tracking variables over response headers
            response.headers["X-Request-ID"] = req_id
            if mission_id:
                response.headers["X-Mission-ID"] = mission_id
                
            return response
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(
                f"[HTTP] {request.method} {request.url.path} failed: {e} in {duration:.4f}s",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "request_id": req_id,
                        "mission_id": mission_id,
                        "duration_sec": duration,
                        "status_code": 500
                    }
                }
            )
            raise e
            
        finally:
            # Safeguard memory leaks by cleaning up the token registers
            request_id_ctx.reset(request_id_token)
            mission_id_ctx.reset(mission_id_token)


class SlidingWindowRateLimiter:
    """
    Lightweight in-memory sliding window rate limiter.
    """
    def __init__(self, limit: int = 60, window_sec: int = 60):
        self.limit = limit
        self.window_sec = window_sec
        self.records = {}
        
    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        if client_ip not in self.records:
            self.records[client_ip] = []
            
        # Keep only timestamps within the sliding window
        self.records[client_ip] = [t for t in self.records[client_ip] if now - t < self.window_sec]
        
        if len(self.records[client_ip]) >= self.limit:
            return False
            
        self.records[client_ip].append(now)
        return True


# Instantiate global rate limiters
claims_rate_limiter = SlidingWindowRateLimiter(limit=60, window_sec=60)
demo_rate_limiter = SlidingWindowRateLimiter(limit=30, window_sec=60)
