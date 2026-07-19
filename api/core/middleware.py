import re
import logging
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.config.config import settings

logger = logging.getLogger(__name__)

BLOCKED_UA_PATTERNS = re.compile(
    r"(python-requests|httpx|curl|wget|scrapy|httpclient|"
    r"java/|okhttp|go-http|node-fetch|axios|postman|insomnia|"
    r"bot|spider|crawl|slurp|semrush|ahrefs|mj12)",
    re.IGNORECASE,
)

ALLOWED_ORIGINS = set(settings.allowed_origins)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path.startswith("/api/") and request.method == "POST":
            rejection = self._check_bot_signals(request)
            if rejection:
                return rejection

        response: Response = await call_next(request)

        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), payment=()"

        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "connect-src 'self' https://api.xposedornot.com https://www.google-analytics.com https://www.googletagmanager.com; "
            "img-src 'self' data: https://api.xposedornot.com https://xposedornot.com https://www.google-analytics.com https://www.googletagmanager.com; "
            "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "frame-ancestors 'none';"
        )

        return response

    def _check_bot_signals(self, request: Request) -> JSONResponse | None:
        user_agent = request.headers.get("user-agent", "")
        if not user_agent or BLOCKED_UA_PATTERNS.search(user_agent):
            logger.warning(f"Blocked suspicious UA: '{user_agent}' from {request.client.host if request.client else 'unknown'}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"status": "error", "detail": "Akses ditolak."},
            )

        origin = request.headers.get("origin", "")
        referer = request.headers.get("referer", "")
        if origin and origin not in ALLOWED_ORIGINS:
            logger.warning(f"Blocked invalid origin: '{origin}'")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"status": "error", "detail": "Akses ditolak."},
            )

        if not origin and not referer:
            logger.warning(f"Blocked request without origin/referer from {request.client.host if request.client else 'unknown'}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"status": "error", "detail": "Akses ditolak."},
            )

        return None
