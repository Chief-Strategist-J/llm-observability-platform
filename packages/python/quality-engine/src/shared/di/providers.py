from __future__ import annotations

from shared.ports.alert_publisher_port import AlertPublisherPort
from infra.adapters.alerts.logger_alert_adapter import LoggerAlertAdapter

def build_alert_publisher() -> AlertPublisherPort:
    return LoggerAlertAdapter()
