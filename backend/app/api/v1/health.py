"""
Health Check Endpoints

Provides health, readiness, and liveness status of the API.
"""

from fastapi import APIRouter, Response, status

from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Return health status of the API.

    Always succeeds if app is running.
    """
    return {"status": "healthy", "version": settings.app_version}


@router.get("/health/live")
async def liveness_check():
    """
    Simple liveness probe.

    Used by orchestrators to check if the app is alive.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_check(response: Response):
    """
    Readiness probe - checks if the app is ready to serve traffic.

    Checks:
    - Data files loaded/accessible
    - Redis connected (if configured)
    - LLM reachable (optional)
    """
    checks = {
        "data": _check_data_files(),
        "redis": await _check_redis(),
        "llm": _check_llm_config(),
    }

    all_ready = all(checks.values())

    if not all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "checks": checks}

    return {"status": "ready", "checks": checks}


def _check_data_files() -> bool:
    """Check if data files exist."""
    try:
        # Check if scores file exists (main data file)
        return settings.scores_path.exists()
    except Exception:
        return False


async def _check_redis() -> bool:
    """Check if Redis is reachable."""
    try:
        import redis.asyncio as redis

        url = settings.redis_url
        if settings.redis_password:
            # Insert password into URL if provided separately
            url = settings.redis_url.replace("://", f"://:{settings.redis_password}@")

        client = redis.from_url(url, decode_responses=True)
        await client.ping()
        await client.close()
        return True
    except Exception:
        return False


def _check_llm_config() -> bool:
    """Check if LLM is configured (not connectivity check)."""
    # Just check if API key is configured
    # Actual connectivity check would be expensive
    return bool(settings.llm_api_key)
