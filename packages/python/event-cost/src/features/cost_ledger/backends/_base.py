from typing import Protocol, runtime_checkable

@runtime_checkable
class Backend(Protocol):
    def record(self, span: "SpanInput", cost_usd_micro: int) -> None:
        ...

    def query_total(self, org_id: str, window: str, **filters) -> int:
        ...

    def get_budget(self, org_id: str, project_id: str) -> int:
        ...

    def set_budget(self, org_id: str, project_id: str, micro: int) -> None:
        ...

    def check_anomaly(self, service_name: str, model: str) -> bool:
        ...
