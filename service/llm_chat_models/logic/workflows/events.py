import asyncio
from typing import Any, Dict, Optional
from telemetry.logger import log_event


class EventBus:
    """
    In-process event bus for agent ↔ workflow communication.

    Supports:
    - send_event(name, payload) — fire an event
    - wait_for_event(name, timeout) — block until event arrives
    - Approval/rejection patterns (approve/reject are just named events)

    This is an in-memory implementation. For production durability at scale,
    swap this for a persistent event queue (Redis, NATS, etc.).
    """

    def __init__(self):
        self._events: Dict[str, asyncio.Event] = {}
        self._payloads: Dict[str, Any] = {}

    async def send_event(self, name: str, payload: Any = None):
        """Dispatch an event by name."""
        self._payloads[name] = payload

        if name not in self._events:
            self._events[name] = asyncio.Event()

        self._events[name].set()
        log_event("event_sent", event_name=name)

    async def wait_for_event(
        self, name: str, timeout: Optional[float] = None
    ) -> Any:
        """
        Block until an event with the given name is dispatched.

        Args:
            name: Event name to wait for.
            timeout: Max seconds to wait. None = wait indefinitely.

        Returns:
            The event payload, or None if no payload was sent.

        Raises:
            asyncio.TimeoutError: If timeout is exceeded.
        """
        if name not in self._events:
            self._events[name] = asyncio.Event()

        log_event("event_waiting", event_name=name, timeout=timeout)

        if timeout is not None:
            await asyncio.wait_for(self._events[name].wait(), timeout=timeout)
        else:
            await self._events[name].wait()

        payload = self._payloads.pop(name, None)
        self._events.pop(name, None)
        log_event("event_received", event_name=name)
        return payload

    async def approve(self, workflow_id: str, payload: Any = None):
        """Shorthand: send an approval event for a workflow."""
        await self.send_event(f"approval:{workflow_id}", {
            "approved": True,
            "payload": payload,
        })

    async def reject(self, workflow_id: str, reason: str = ""):
        """Shorthand: send a rejection event for a workflow."""
        await self.send_event(f"approval:{workflow_id}", {
            "approved": False,
            "reason": reason,
        })

    async def wait_for_approval(
        self, workflow_id: str, timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Block until approval or rejection for a workflow.

        Returns:
            Dict with 'approved' bool and optional 'payload' or 'reason'.

        Raises:
            asyncio.TimeoutError if timeout exceeded.
        """
        return await self.wait_for_event(
            f"approval:{workflow_id}", timeout=timeout
        )

    def clear(self):
        """Clear all pending events."""
        self._events.clear()
        self._payloads.clear()
