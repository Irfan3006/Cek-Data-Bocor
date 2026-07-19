import time
import threading
from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    PENALTY_WINDOWS = [60, 120, 300]

    def __init__(self, requests_limit: int = 10, window_seconds: int = 60) -> None:
        self.requests_limit = requests_limit
        self.base_window = window_seconds
        self._requests: dict[str, list[float]] = {}
        self._violations: dict[str, int] = {}
        self._lock = threading.Lock()

    def _get_window_for_ip(self, ip: str) -> int:
        violation_count = self._violations.get(ip, 0)
        index = min(violation_count, len(self.PENALTY_WINDOWS) - 1)
        return self.PENALTY_WINDOWS[index]

    def check_rate_limit(self, ip: str) -> None:
        now = time.time()
        with self._lock:
            self._cleanup_expired(now)

            window = self._get_window_for_ip(ip)
            history = self._requests.get(ip, [])
            cutoff = now - window
            history = [ts for ts in history if ts > cutoff]

            if len(history) >= self.requests_limit:
                self._violations[ip] = self._violations.get(ip, 0) + 1
                new_window = self._get_window_for_ip(ip)
                wait_time = max(1, int(history[0] + new_window - now))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Terlalu banyak permintaan. Silakan coba lagi dalam {wait_time} detik.",
                    headers={"Retry-After": str(wait_time)}
                )

            history.append(now)
            self._requests[ip] = history

    def _cleanup_expired(self, now: float) -> None:
        max_window = max(self.PENALTY_WINDOWS)
        expired_ips = [
            ip for ip, history in self._requests.items()
            if not history or history[-1] < now - max_window
        ]
        for ip in expired_ips:
            del self._requests[ip]
            self._violations.pop(ip, None)


limiter = InMemoryRateLimiter(requests_limit=10, window_seconds=60)


async def rate_limit_dependency(request: Request) -> None:
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown-ip"

    limiter.check_rate_limit(client_ip)
