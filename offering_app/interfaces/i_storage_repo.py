from abc import ABC, abstractmethod
from typing import Any

from offering_app.models.offering import Offering


class IStorageRepo(ABC):
    @abstractmethod
    def save(self, offering: Offering) -> str:
        """Persist an offering and return its identifier."""

    @abstractmethod
    def get_by_date(self, service_date: str) -> list[dict[str, Any]]:
        """Return offerings for a given service date."""
