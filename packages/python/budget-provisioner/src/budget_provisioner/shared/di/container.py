from budget_provisioner.config import Config, load_config
from budget_provisioner.infra.adapters.postgres.postgres_adapter import PostgresAdapter
from budget_provisioner.infra.adapters.redis.redis_adapter import RedisAdapter
from budget_provisioner.infra.adapters.metrics.prometheus_adapter import PrometheusAdapter
from budget_provisioner.features.budget_management.service import BudgetManagementService
from budget_provisioner.infra.auth import JWTAuthenticator

class Container:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or load_config()
        self.postgres_adapter = PostgresAdapter(self.config.postgres_dsn)
        self.redis_adapter = RedisAdapter(self.config.redis_url)
        self.metrics_adapter = PrometheusAdapter()
        self.budget_service = BudgetManagementService(
            db_port=self.postgres_adapter,
            redis_port=self.redis_adapter,
            metrics_port=self.metrics_adapter
        )
        self.authenticator = JWTAuthenticator(self.config.internal_jwt_secret)
