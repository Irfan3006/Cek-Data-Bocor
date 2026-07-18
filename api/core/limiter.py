import time
import threading
from fastapi import HTTPException, Request, status

class InMemoryRateLimiter:
    def __init__(self, requests_limit: int = 10, window_seconds: int = 60) -> None:
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def check_rate_limit(self, ip: str) -> None:
        """
        Memeriksa apakah IP melebih batas rate limit.
        Melemparkan HTTPException 429 jika melebihi batas.
        """
        now = time.time()
        with self._lock:
            history = self._requests.get(ip, [])
            
            cutoff = now - self.window_seconds
            history = [timestamp for timestamp in history if timestamp > cutoff]
            
            if len(history) >= self.requests_limit:
                wait_time = int(history[0] + self.window_seconds - now)
                if wait_time < 1:
                    wait_time = 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Terlalu banyak permintaan. Silakan coba lagi dalam {wait_time} detik.",
                    headers={"Retry-After": str(wait_time)}
                )
            
            history.append(now)
            self._requests[ip] = history

limiter = InMemoryRateLimiter(requests_limit=10, window_seconds=60)

async def rate_limit_dependency(request: Request) -> None:
    """FastAPI Dependency untuk memvalidasi rate limit berdasarkan IP client."""
    # Vercel meneruskan IP asli melalui header 'x-forwarded-for' atau 'x-real-ip'
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        # Jika x-forwarded-for memiliki beberapa IP (seperti ip_client, proxy1, proxy2)
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown-ip"
        
    limiter.check_rate_limit(client_ip)
