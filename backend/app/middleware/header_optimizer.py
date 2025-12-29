"""
Header optimization middleware for Cloudflare quick tunnels
Ensures headers stay under 8KB limit
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)

# Quick tunnel header limit (conservative estimate)
MAX_HEADER_SIZE = 6 * 1024  # 6KB to be safe (actual limit ~8KB)


class HeaderOptimizationMiddleware(BaseHTTPMiddleware):
    """Optimize headers to work with Cloudflare quick tunnel limitations"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Calculate total header size
        total_size = sum(
            len(k) + len(v)
            for k, v in response.headers.items()
        )

        if total_size > MAX_HEADER_SIZE:
            logger.warning(
                f"Response headers too large: {total_size} bytes "
                f"(limit: {MAX_HEADER_SIZE}). Trimming..."
            )

            # Keep only critical headers
            critical_headers = {
                'content-type': response.headers.get('content-type'),
                'content-length': response.headers.get('content-length'),
                'access-control-allow-origin': '*',
                'access-control-allow-methods': '*',
                'access-control-allow-headers': '*',
            }

            # Create new response with minimal headers
            new_response = Response(
                content=response.body,
                status_code=response.status_code,
                headers={k: v for k, v in critical_headers.items() if v},
                media_type=response.headers.get('content-type')
            )

            new_size = sum(len(k) + len(v) for k, v in new_response.headers.items())
            logger.info(f"Headers trimmed: {total_size} → {new_size} bytes")

            return new_response

        return response
