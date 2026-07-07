from typing import Protocol, List, Tuple

class TimesFMPort(Protocol):
    def forecast(
        self,
        series: List[float],
        horizon: int = 24
    ) -> Tuple[List[float], List[float], List[float]]:
        """
        Runs forecast on the input series.
        Returns:
            mean: forecasted mean values of length `horizon`
            p10: forecasted p10 values of length `horizon`
            p90: forecasted p90 values of length `horizon`
        """
        ...
