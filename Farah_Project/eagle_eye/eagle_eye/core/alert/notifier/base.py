from abc import ABC, abstractmethod

from ..event import AlertEvent
from ..snapshot import AlertSnapshot


class NotificationProvider(ABC):
    @abstractmethod
    def send(self, event: AlertEvent, snapshot: AlertSnapshot) -> None: ...
