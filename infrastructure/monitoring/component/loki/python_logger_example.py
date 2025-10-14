import logging
from logging.handlers import TimedRotatingFileHandler
import json
import os

class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "message": record.getMessage()
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)

def setup_logging(log_path):
    """
    Set up JSON logging to a rotating file.

    Args:
        log_path: Path to the log file (e.g., "component/grafana/storage/development/myapp/app.log")
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    handler = TimedRotatingFileHandler(log_path, when="midnight", backupCount=7)
    handler.setFormatter(JsonFormatter())

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Avoid double adding handlers in long-running processes
    if not any(isinstance(h, TimedRotatingFileHandler) and getattr(h, "baseFilename", "") == log_path for h in logger.handlers):
        logger.addHandler(handler)

# Example usage for different environments:
#
# For Development:
# setup_logging("component/grafana/storage/development/myapp/app.log")
#
# For Staging:
# setup_logging("component/grafana/storage/staging/myapp/app.log")
#
# For Production:
# setup_logging("component/grafana/storage/production/myapp/app.log")
#
# Then use normal logging:
# import logging
# logging.info("Application started successfully")
# logging.error("Something went wrong", extra={"user_id": 123})
