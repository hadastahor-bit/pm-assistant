import asyncio
from typing import Optional, Dict
from .base import SessionStore
from ..models.session import Session


class InMemorySessionStore(SessionStore):
    """
    Thread-safe in-memory store for development and Render free-tier deployments.
    State is scoped to the running process — sessions survive restarts only if the
    process keeps running (Render free tier keeps the process alive while active).
    """

    def __init__(self):
        self._store: Dict[str, dict] = {}
        self._lock = asyncio.Lock()

    async def get(self, session_id: str) -> Optional[Session]:
        async with self._lock:
            data = self._store.get(session_id)
            return Session(**data) if data else None

    async def save(self, session: Session) -> None:
        async with self._lock:
            self._store[session.session_id] = session.model_dump(mode="json")

    async def delete(self, session_id: str) -> None:
        async with self._lock:
            self._store.pop(session_id, None)
