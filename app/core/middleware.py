import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.core.logging_config import logger


class TimingLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        """Middleware que logea método, path, status, tiempo y IP."""
        start_time = time.perf_counter()
        ip = request.client.host if request.client else "unknown"

        response = await call_next(request)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} "
            f"({elapsed_ms:.1f}ms) [{ip}]"
        )
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"
        return response