"""In-memory TTL cache for city lookups and other repeated queries."""

import logging
import time
from threading import Lock
from typing import Any, Optional

from qweather_mcp_server.core.config import CACHE_TTL_SECONDS

logger = logging.getLogger("hefeng_qweather_mcp")


class TTLCache:
    """Simple thread-safe in-memory cache with per-entry TTL."""

    def __init__(self, ttl: int = CACHE_TTL_SECONDS):
        self._ttl = ttl
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            ts, value = entry
            if time.time() - ts > self._ttl:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._store[key] = (time.time(), value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


# Module-level singleton
geo_cache = TTLCache()
