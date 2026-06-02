from __future__ import annotations

import logging

logger = logging.getLogger("quality-engine.alerts")

class LoggerAlertAdapter:
    def publish_alert(self, message: str, metadata: dict[str, str] | None = None) -> None:
        extra = {"metadata": metadata} if metadata else {}
        logger.error(f"ALERT: {message} | {extra}")
