import time
from typing import Dict, Any, Optional

class InMemoryTTLCache:
    """
    Simple thread-safe in-memory cache with TTL support for AI explanations.
    """
    def __init__(self, default_ttl_seconds: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            entry = self.cache[key]
            if entry["expiry"] > time.time():
                return entry["value"]
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        expiry = time.time() + (ttl if ttl is not None else self.default_ttl)
        self.cache[key] = {
            "value": value,
            "expiry": expiry
        }

    def clear(self) -> None:
        self.cache.clear()

# Global cache instance for the application lifecycle
ai_cache = InMemoryTTLCache(default_ttl_seconds=3600)
