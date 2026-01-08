from enum import Enum


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    WARNING = "warning"
    CRITICAL = "critical"
