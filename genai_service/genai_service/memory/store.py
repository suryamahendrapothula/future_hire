"""In-memory session store for quick lookups alongside LangGraph checkpoints."""

from __future__ import annotations

import asyncio
from typing import Any


class MemoryStore:
    """Thread-safe async in-memory key-value store."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._data[key] = value

    async def get(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            return self._data.get(key, default)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._data.pop(key, None)

    async def exists(self, key: str) -> bool:
        async with self._lock:
            return key in self._data

    async def keys(self, prefix: str = "") -> list[str]:
        async with self._lock:
            if not prefix:
                return list(self._data.keys())
            return [k for k in self._data if k.startswith(prefix)]


_store: MemoryStore | None = None


def get_memory_store() -> MemoryStore:
    global _store
    if _store is None:
        _store = MemoryStore()
    return _store
