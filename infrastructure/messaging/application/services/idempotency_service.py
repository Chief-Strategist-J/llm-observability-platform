from domain.ports.idempotency_port import IdempotencyPort
from application.api.v1.error_handler import raise_conflict_error, raise_validation_error


class IdempotencyService:
    def __init__(self, idempotency_store: IdempotencyPort):
        self._idempotency_store = idempotency_store

    async def check_and_handle_duplicate(self, event_id: str) -> None:
        if not event_id:
            return

        try:
            is_duplicate = not await self._idempotency_store.check_and_store(event_id)
            if is_duplicate:
                raise_conflict_error(f"Duplicate event_id: {event_id}")
        except ValueError as e:
            raise_validation_error(str(e))
