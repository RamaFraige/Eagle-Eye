from dataclasses import dataclass
from typing import Dict

from .severity import AlertSeverity


@dataclass(frozen=True)
class AlertEvent:
    name: str
    stream_id: str
    severity: AlertSeverity
    triggered_rules: list[str]
    metadata: Dict
    timestamp: float

    @property
    def rule_name(self) -> str:
        return ", ".join(self.triggered_rules)
