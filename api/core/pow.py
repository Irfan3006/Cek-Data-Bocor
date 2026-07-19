import hashlib
import hmac
import os
import time
import threading

from api.config.config import settings


class ChallengeManager:
    def __init__(self) -> None:
        self._used_challenges: dict[str, float] = {}
        self._lock = threading.Lock()

    def _sign_challenge(self, challenge: str, timestamp: float) -> str:
        message = f"{challenge}:{timestamp}"
        return hmac.new(
            settings.pow_secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

    def generate_challenge(self) -> dict:
        challenge = os.urandom(16).hex()
        timestamp = time.time()
        token = self._sign_challenge(challenge, timestamp)

        return {
            "challenge": challenge,
            "difficulty": settings.pow_difficulty,
            "token": f"{token}:{timestamp}",
        }

    def validate_solution(self, challenge: str, nonce: int, token: str) -> bool:
        try:
            signature, timestamp_str = token.rsplit(":", 1)
            timestamp = float(timestamp_str)
        except (ValueError, AttributeError):
            return False

        if time.time() - timestamp > settings.pow_ttl_seconds:
            return False

        expected_signature = self._sign_challenge(challenge, timestamp)
        if not hmac.compare_digest(signature, expected_signature):
            return False

        with self._lock:
            if token in self._used_challenges:
                return False
            self._used_challenges[token] = time.time()
            self._cleanup_expired()

        target_prefix = "0" * settings.pow_difficulty
        test_hash = hashlib.sha256(f"{challenge}:{nonce}".encode()).hexdigest()
        return test_hash.startswith(target_prefix)

    def _cleanup_expired(self) -> None:
        cutoff = time.time() - settings.pow_ttl_seconds
        expired_keys = [k for k, v in self._used_challenges.items() if v < cutoff]
        for key in expired_keys:
            del self._used_challenges[key]


challenge_manager = ChallengeManager()
