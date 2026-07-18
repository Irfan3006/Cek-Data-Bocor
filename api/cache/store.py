import time
import threading
from typing import Any, Optional

class InMemoryCache:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Dapatkan data dari cache jika kunci ada dan belum kedaluwarsa."""
        normalized_key = key.strip().lower()
        with self._lock:
            if normalized_key not in self._cache:
                return None
            
            data, expires_at = self._cache[normalized_key]
            if time.time() > expires_at:
                # Lazy delete jika kedaluwarsa
                del self._cache[normalized_key]
                return None
                
            return data

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Simpan data ke dalam cache dengan TTL tertentu."""
        normalized_key = key.strip().lower()
        expires_at = time.time() + ttl_seconds
        with self._lock:
            self._cache[normalized_key] = (value, expires_at)

    def delete(self, key: str) -> None:
        """Hapus data dari cache secara manual."""
        normalized_key = key.strip().lower()
        with self._lock:
            if normalized_key in self._cache:
                del self._cache[normalized_key]

    def clear(self) -> None:
        """Hapus seluruh isi cache."""
        with self._lock:
            self._cache.clear()

# Global cache store instance
cache_store = InMemoryCache()
