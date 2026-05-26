class WorkerError(Exception):
    pass


class ValidationError(WorkerError):
    pass


class ClickHouseQueryError(WorkerError):
    pass


class DatabaseConnectionError(WorkerError):
    pass
