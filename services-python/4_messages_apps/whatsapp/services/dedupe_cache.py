"""
Cache em memória para dedupe de webhooks (TTL). Não é banco de produto.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Optional


class DedupeCache:
    """Set com TTL dos external_ids já encaminhados."""

    def __init__(self, ttl_seconds: int = 600, max_size: int = 5000):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._items: OrderedDict[str, float] = OrderedDict()
        self._lock = threading.Lock()

    def _purge_expired(self, now: float) -> None:
        expired = [k for k, exp in self._items.items() if exp <= now]
        for k in expired:
            del self._items[k]

    def seen_or_add(self, key: str) -> bool:
        """
        Retorna True se a chave já existia (duplicata).
        Se for nova, adiciona e retorna False.
        """
        if not key:
            return False
        now = time.time()
        with self._lock:
            self._purge_expired(now)
            if key in self._items:
                # refresh TTL
                self._items.move_to_end(key)
                self._items[key] = now + self.ttl_seconds
                return True
            self._items[key] = now + self.ttl_seconds
            while len(self._items) > self.max_size:
                self._items.popitem(last=False)
            return False


class RecentEventsBuffer:
    """Ring buffer dos últimos eventos (ops do gateway)."""

    def __init__(self, limit: int = 50):
        self.limit = max(1, limit)
        self._events: list[dict] = []
        self._lock = threading.Lock()

    def add(self, event: dict) -> None:
        with self._lock:
            self._events.append(event)
            if len(self._events) > self.limit:
                self._events = self._events[-self.limit :]

    def list(self, limit: Optional[int] = None) -> list[dict]:
        with self._lock:
            n = limit if limit is not None else self.limit
            return list(reversed(self._events[-n:]))
