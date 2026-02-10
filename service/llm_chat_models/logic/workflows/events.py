import asyncio
from typing import Any, Dict, Optional
from logic.persistence.mongo_store import MongoWorkflowStore
from config.settings import EVENT_POLL_INTERVAL
from telemetry.logger import log_event

class EventBus:

    def __init__(self, store: Optional[MongoWorkflowStore]=None):
        self._store = store or MongoWorkflowStore()
        self._local_events: Dict[str, asyncio.Event] = {}
        self._local_payloads: Dict[str, Any] = {}

    async def send_event(self, name: str, payload: Any=None):
        self._store.save_event(name, payload)
        self._local_payloads[name] = payload
        if name not in self._local_events:
            self._local_events[name] = asyncio.Event()
        self._local_events[name].set()
        log_event('event_sent', event_name=name)

    async def wait_for_event(self, name: str, timeout: Optional[float]=None) -> Any:
        log_event('event_waiting', event_name=name, timeout=timeout)
        if name in self._local_events and self._local_events[name].is_set():
            payload = self._local_payloads.pop(name, None)
            self._local_events.pop(name, None)
            log_event('event_received_local', event_name=name)
            return payload
        elapsed = 0.0
        poll_interval = EVENT_POLL_INTERVAL
        while True:
            doc = self._store.poll_event(name)
            if doc:
                self._store.ack_event(doc['_id'])
                log_event('event_received_mongo', event_name=name)
                return doc.get('payload')
            if name in self._local_events:
                try:
                    await asyncio.wait_for(self._local_events[name].wait(), timeout=poll_interval)
                    payload = self._local_payloads.pop(name, None)
                    self._local_events.pop(name, None)
                    log_event('event_received_local', event_name=name)
                    return payload
                except asyncio.TimeoutError:
                    pass
            else:
                await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            if timeout is not None and elapsed >= timeout:
                raise asyncio.TimeoutError(f"Timed out waiting for event '{name}' after {timeout}s")

    async def approve(self, workflow_id: str, payload: Any=None):
        await self.send_event(f'approval:{workflow_id}', {'approved': True, 'payload': payload})

    async def reject(self, workflow_id: str, reason: str=''):
        await self.send_event(f'approval:{workflow_id}', {'approved': False, 'reason': reason})

    async def wait_for_approval(self, workflow_id: str, timeout: Optional[float]=None) -> Dict[str, Any]:
        return await self.wait_for_event(f'approval:{workflow_id}', timeout=timeout)

    def clear(self):
        self._local_events.clear()
        self._local_payloads.clear()