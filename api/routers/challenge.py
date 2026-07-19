from fastapi import APIRouter, Request, HTTPException, status
from api.core.pow import challenge_manager
from api.core.limiter import InMemoryRateLimiter

router = APIRouter()

challenge_limiter = InMemoryRateLimiter(requests_limit=30, window_seconds=60)


@router.get("/challenge", tags=["Security"])
async def get_challenge(request: Request) -> dict:
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown-ip"

    challenge_limiter.check_rate_limit(client_ip)

    return challenge_manager.generate_challenge()
