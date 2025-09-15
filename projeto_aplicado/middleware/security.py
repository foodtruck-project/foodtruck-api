"""Security middleware for additional protection."""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add basic security headers to all responses and handle HTTPS detection."""

    async def dispatch(self, request: Request, call_next):
        # Ensure FastAPI knows we're behind HTTPS when X-Forwarded-Proto is https
        if request.headers.get("X-Forwarded-Proto") == "https":
            # Modify the request URL scheme to https for proper OpenAPI generation
            request.scope["scheme"] = "https"

        response: Response = await call_next(request)

        # Basic security headers only
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response
