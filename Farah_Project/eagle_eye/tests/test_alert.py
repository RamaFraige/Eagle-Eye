import asyncio
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from eagle_eye.core.alert.buffer.registry import VideoBufferRegistry
from eagle_eye.core.alert.event import AlertEvent
from eagle_eye.core.alert.manager import AlertManager
from eagle_eye.core.alert.notifier import LocalFileProvider, NotificationProvider
from eagle_eye.core.alert.rules import (
    AlertRule,
    ConfidenceRule,
    DetectionMatchRule,
)
from eagle_eye.core.alert.severity import AlertSeverity
from eagle_eye.core.alert.snapshot import AlertSnapshot


# Mock Rules for Testing
class AlwaysTrueRule(AlertRule):
    def __init__(self, name: str = "AlwaysTrue"):
        self.name = name
        self.severity = AlertSeverity.LOW

    def evaluate(self, result: dict, stream_id: str) -> bool:
        return True


class AlwaysFalseRule(AlertRule):
    def __init__(self, name: str = "AlwaysFalse"):
        self.name = name
        self.severity = AlertSeverity.WARNING

    def evaluate(self, result: dict, stream_id: str) -> bool:
        return False


class MockNotifier(NotificationProvider):
    def __init__(self):
        self.sent_events = []

    def send(self, event: AlertEvent, video: bytes) -> None:
        self.sent_events.append((event, video))


@pytest.fixture
def buffer_registry():
    return VideoBufferRegistry(seconds=5, fps=10)


@pytest.fixture
def mock_notifier():
    return MockNotifier()


@pytest.fixture
def temp_dir():
    with TemporaryDirectory() as tmpdir:
        yield tmpdir


# ============================================================================
# AlertManager Tests
# ============================================================================


@pytest.mark.asyncio
async def test_alert_manager_all_rules_must_pass(buffer_registry, mock_notifier):
    """Test that AlertManager only fires when ALL rules pass"""
    rule1 = AlwaysTrueRule("Rule1")
    rule2 = AlwaysFalseRule("Rule2")

    manager = AlertManager(
        rules=[rule1, rule2],
        notifier=mock_notifier,
        buffers=buffer_registry,
        cooldown_sec=0,
    )

    manager.process("stream1", b"frame", {})
    await asyncio.sleep(0.01)

    assert len(mock_notifier.sent_events) == 0, "Should not alert when one rule fails"


@pytest.mark.asyncio
async def test_alert_manager_all_true_fires_alert(buffer_registry, mock_notifier):
    """Test that AlertManager fires when all rules pass"""
    rule1 = AlwaysTrueRule("Rule1")
    rule2 = AlwaysTrueRule("Rule2")

    manager = AlertManager(
        rules=[rule1, rule2],
        notifier=mock_notifier,
        buffers=buffer_registry,
        cooldown_sec=0,
    )

    manager.process("stream1", b"frame", {})
    await asyncio.sleep(0.01)

    assert len(mock_notifier.sent_events) == 1, "Should alert when all rules pass"
    event, video = mock_notifier.sent_events[0]
    assert "Rule1" in event.triggered_rules
    assert "Rule2" in event.triggered_rules
    assert event.rule_name == "Rule1, Rule2"


@pytest.mark.asyncio
async def test_alert_manager_cooldown(buffer_registry, mock_notifier):
    """Test that cooldown prevents rapid alerts"""
    rule = AlwaysTrueRule()

    manager = AlertManager(
        rules=[rule], notifier=mock_notifier, buffers=buffer_registry, cooldown_sec=0.5
    )

    # First alert should fire
    manager.process("stream1", b"frame1", {})
    await asyncio.sleep(0.01)
    assert len(mock_notifier.sent_events) == 1

    # Second alert should be blocked by cooldown
    manager.process("stream1", b"frame2", {})
    await asyncio.sleep(0.01)
    assert len(mock_notifier.sent_events) == 1, "Cooldown should prevent second alert"

    # Wait for cooldown to expire
    time.sleep(0.6)

    # Third alert should fire
    manager.process("stream1", b"frame3", {})
    await asyncio.sleep(0.01)
    assert len(mock_notifier.sent_events) == 2, "Alert should fire after cooldown"


# ============================================================================
# Rule Tests
# ============================================================================


def test_detection_match_rule_any():
    """Test DetectionMatchRule with match_mode='any'"""
    rule = DetectionMatchRule(trigger_classes=["gun", "knife"], match_mode="any")

    # Match one
    assert rule.evaluate({"detections": [{"class_name": "gun"}]}, "stream1") is True
    # Match other
    assert rule.evaluate({"detections": [{"class_name": "knife"}]}, "stream1") is True
    # Match none
    assert rule.evaluate({"detections": [{"class_name": "person"}]}, "stream1") is False


def test_detection_match_rule_all():
    """Test DetectionMatchRule with match_mode='all'"""
    rule = DetectionMatchRule(trigger_classes=["gun", "knife"], match_mode="all")

    # Match one (fail)
    assert rule.evaluate({"detections": [{"class_name": "gun"}]}, "stream1") is False

    # Match all (pass)
    result = {
        "detections": [
            {"class_name": "gun"},
            {"class_name": "knife"},
        ]
    }
    assert rule.evaluate(result, "stream1") is True


def test_confidence_rule():
    """Test ConfidenceRule"""
    rule = ConfidenceRule(min_confidence=0.8, match_mode="any")

    # High confidence
    assert rule.evaluate({"detections": [{"confidence": 0.9}]}, "stream1") is True

    # Low confidence
    assert rule.evaluate({"detections": [{"confidence": 0.5}]}, "stream1") is False


@pytest.mark.asyncio
async def test_local_file_provider_multiple_alerts(temp_dir):
    """Test that multiple alerts create separate folders"""
    provider = LocalFileProvider(temp_dir)

    for i in range(3):
        event = AlertEvent(
            name="Alert",
            stream_id=f"stream{i}",
            severity=AlertSeverity.LOW,
            triggered_rules=[f"Rule{i}"],
            metadata={},
            timestamp=time.time(),
        )
        provider.send(event, AlertSnapshot(b"video"))
        time.sleep(1.1)  # Ensure different timestamps

    base_path = Path(temp_dir)
    folders = list(base_path.iterdir())
    assert len(folders) == 3, "Should create three separate folders"


# ============================================================================
# AlertEvent Tests
# ============================================================================


def test_alert_event_rule_name_property():
    """Test that rule_name is computed from triggered_rules"""
    event = AlertEvent(
        name="Alert",
        stream_id="test",
        severity=AlertSeverity.WARNING,
        triggered_rules=["Rule1", "Rule2", "Rule3"],
        metadata={},
        timestamp=time.time(),
    )

    assert event.rule_name == "Rule1, Rule2, Rule3"


def test_alert_event_single_rule():
    """Test AlertEvent with single rule"""
    event = AlertEvent(
        name="Alert",
        stream_id="test",
        severity=AlertSeverity.CRITICAL,
        triggered_rules=["SingleRule"],
        metadata={"detection": "gun"},
        timestamp=time.time(),
    )

    assert event.rule_name == "SingleRule"
    assert len(event.triggered_rules) == 1
