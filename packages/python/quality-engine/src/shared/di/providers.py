from __future__ import annotations

from shared.ports.alert_publisher_port import AlertPublisherPort
from shared.ports.scorer_client_port import ScorerClientPort
from infra.adapters.alerts.logger_alert_adapter import LoggerAlertAdapter
from infra.adapters.scorers.http_scorer_client_adapter import HttpScorerClientAdapter

def build_alert_publisher() -> AlertPublisherPort:
    return LoggerAlertAdapter()

def build_scorer_client() -> ScorerClientPort:
    return HttpScorerClientAdapter()
