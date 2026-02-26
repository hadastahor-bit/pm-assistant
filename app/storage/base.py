from abc import ABC, abstractmethod
from typing import Optional
from ..models.session import Session


class SessionStore(ABC):
    @abstractmethod
    async def get(self, session_id: str) -> Optional[Session]: ...

    @abstractmethod
    async def save(self, session: Session) -> None: ...

    @abstractmethod
    async def delete(self, session_id: str) -> None: ...
