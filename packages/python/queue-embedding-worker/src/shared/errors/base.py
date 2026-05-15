class WorkerError(Exception):
    """Base class for queue worker errors."""


class ValidationError(WorkerError):
    """Raised when inputs/config are invalid."""
