import os
from shared.ports.alert_publisher_port import AlertPublisherPort
from shared.ports.scorer_client_port import ScorerClientPort
from shared.ports.quality_score_repo_port import QualityScoreRepositoryPort
from infra.adapters.alerts.logger_alert_adapter import LoggerAlertAdapter
from infra.adapters.scorers.http_scorer_client_adapter import HttpScorerClientAdapter
from infra.adapters.postgres.postgres_adapter import PostgresQualityScoreAdapter

def build_alert_publisher() -> AlertPublisherPort:
    return LoggerAlertAdapter()

def build_scorer_client() -> ScorerClientPort:
    return HttpScorerClientAdapter()

def build_quality_score_repo() -> QualityScoreRepositoryPort:
    postgres_user = os.environ.get("POSTGRES_USER", "postgres")
    postgres_password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    postgres_host = os.environ.get("POSTGRES_HOST", "localhost")
    postgres_port = os.environ.get("POSTGRES_PORT", "5432")
    postgres_db = os.environ.get("POSTGRES_DB", "quality_engine_db")
    dsn = os.environ.get(
        "POSTGRES_DSN",
        f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
    )
    return PostgresQualityScoreAdapter(dsn=dsn)
