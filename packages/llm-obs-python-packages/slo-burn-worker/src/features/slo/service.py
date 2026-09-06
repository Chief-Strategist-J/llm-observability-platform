import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class SloService:
    @staticmethod
    def get_window_buckets(now_bucket: int, window_size: int) -> List[int]:
        return [now_bucket - window_size + i for i in range(window_size)]

    @staticmethod
    def compute_burn_rate(errors: int, total: int, slo_threshold: float) -> float:
        if total == 0:
            return 0.0
        error_rate = errors / total
        slo_eb = 1.0 - slo_threshold
        if slo_eb <= 0.0:
            return 0.0
        return error_rate / slo_eb

    @staticmethod
    def determine_severity(fast: float, medium: float, slow: float) -> Optional[str]:
        # 'page': burn_rate_fast > 14.4 AND burn_rate_medium > 6.0
        is_page = fast > 14.4 and medium > 6.0
        if is_page:
            return "page"
        # 'slack': NOT page AND burn_rate_medium > 6.0 AND burn_rate_slow > 3.0
        is_slack = medium > 6.0 and slow > 3.0
        if is_slack:
            return "slack"
        # 'ticket': NOT page AND NOT slack AND burn_rate_slow > 1.0
        is_ticket = slow > 1.0
        if is_ticket:
            return "ticket"
        return None

    @staticmethod
    def compute_budget_remaining_pct(errors_30d: int, total_calls_30d: int, slo_threshold: float) -> float:
        eb_fraction = 1.0 - slo_threshold
        budget = total_calls_30d * eb_fraction
        if budget <= 0:
            return 100.0 if errors_30d == 0 else 0.0
        pct = ((budget - errors_30d) / budget) * 100.0
        return max(0.0, min(100.0, pct))
