import numpy as np
import logging
from typing import List, Tuple
from shared.ports.timesfm_port import TimesFMPort

logger = logging.getLogger(__name__)

class TimesFMAdapter(TimesFMPort):
    def __init__(self, repo_id: str = "google/timesfm-1.0-200m", backend: str = "cpu"):
        self.repo_id = repo_id
        self.backend = backend
        self.model = None
        self.is_mock = True

        try:
            import torch
            import timesfm
            logger.info("Initializing TimesFM model from %s with backend %s", repo_id, backend)
            if hasattr(timesfm, "TimesFM_2p5_200M_torch"):
                self.model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(repo_id)
                self.model.compile(
                    timesfm.ForecastConfig(
                        max_context=1024,
                        max_horizon=256,
                        normalize_inputs=True,
                        use_continuous_quantile_head=True,
                        force_flip_invariance=True,
                        infer_is_positive=True,
                        fix_quantile_crossing=True,
                    )
                )
                self.is_mock = False
            elif hasattr(timesfm, "TimesFm"):
                self.model = timesfm.TimesFm(
                    context_len=168,
                    horizon=24,
                    input_patch_len=32,
                    output_patch_len=128,
                    num_layers=20,
                    model_dims=1280,
                    backend=backend,
                )
                self.model.load_from_checkpoint(repo_id=repo_id)
                self.is_mock = False
            else:
                logger.warning("TimesFM class not found in timesfm module, using mock.")
        except Exception as e:
            logger.warning("Failed to initialize proper TimesFM model, using mock fallback. Error: %s", e)

    def forecast(
        self,
        series: List[float],
        horizon: int = 24
    ) -> Tuple[List[float], List[float], List[float]]:
        if len(series) == 0:
            return [0.0] * horizon, [0.0] * horizon, [0.0] * horizon

        if self.is_mock or self.model is None:
            avg_val = sum(series) / len(series)
            mean_forecast = [avg_val] * horizon
            p10_forecast = [avg_val * 0.8] * horizon
            p90_forecast = [avg_val * 1.2] * horizon
            return mean_forecast, p10_forecast, p90_forecast

        try:
            inputs = [np.array(series, dtype=np.float32)]
            if hasattr(self.model, "forecast"):
                # Check if it's 2.5 config version
                import timesfm
                if hasattr(timesfm, "ForecastConfig"):
                    point_forecast, quantile_forecast = self.model.forecast(
                        horizon=horizon,
                        inputs=inputs,
                    )
                    mean_forecast = point_forecast[0].tolist()
                    p10_forecast = quantile_forecast[0, :, 0].tolist()
                    p90_forecast = quantile_forecast[0, :, -1].tolist()
                    return mean_forecast, p10_forecast, p90_forecast
                else:
                    point_forecast, quantile_forecast = self.model.forecast(inputs, [0])
                    mean_forecast = point_forecast[0].tolist()
                    p10_forecast = quantile_forecast[0, :, 1].tolist()
                    p90_forecast = quantile_forecast[0, :, 9].tolist()
                    return mean_forecast, p10_forecast, p90_forecast
            else:
                raise AttributeError("Model does not have a forecast method.")
        except Exception as e:
            logger.warning("Error running real TimesFM inference, using mock fallback: %s", e)
            avg_val = sum(series) / len(series)
            return [avg_val] * horizon, [avg_val * 0.8] * horizon, [avg_val * 1.2] * horizon
