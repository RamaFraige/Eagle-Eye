from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class AlertRule(ABC):
    name: str

    @abstractmethod
    def evaluate(self, result: dict, stream_id: str) -> bool: ...

    def cleanup(self, stream_id: str) -> None:
        """Optional: Clean up state after an alert is fired."""
        pass
