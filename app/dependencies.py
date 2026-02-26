from functools import lru_cache
from anthropic import AsyncAnthropic
from .config import get_settings
from .storage.base import SessionStore
from .storage.memory_store import InMemorySessionStore

settings = get_settings()

# Single shared store instance (module-level singleton)
_session_store: SessionStore = InMemorySessionStore()


def get_claude_client() -> AsyncAnthropic:
    return AsyncAnthropic(api_key=settings.anthropic_api_key)


def get_session_store() -> SessionStore:
    return _session_store
