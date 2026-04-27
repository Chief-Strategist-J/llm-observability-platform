from domain.ports.persistence_strategy import PersistenceStrategy
from domain.ports.database_port import EventRecord
from domain.ports.event_writer_port import EventWriterPort


class DirectPersistenceStrategy(PersistenceStrategy):
    def __init__(self, database: EventWriterPort):
        self._database = database

    async def save(self, event: EventRecord) -> str:
        return self._database.save_event(event)

    async def save_batch(self, events: list) -> list:
        return self._database.save_events_batch(events)
