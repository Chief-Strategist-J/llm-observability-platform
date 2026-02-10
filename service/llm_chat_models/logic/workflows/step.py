import asyncio
from typing import Any, Callable, Coroutine, Dict, Optional
from telemetry.logger import log_event
from .events import EventBus

class Step:

    def __init__(self, workflow_id: str, event_bus: EventBus, completed_steps: Dict[str, Any], store=None, agent_state_callback: Optional[Callable]=None, progress_callback: Optional[Callable]=None):
        self.workflow_id = workflow_id
        self._event_bus = event_bus
        self._completed: Dict[str, Any] = completed_steps
        self._store = store
        self._agent_state_cb = agent_state_callback
        self._progress_cb = progress_callback

    async def do(self, name: str, fn: Callable[..., Coroutine], *, retries: int=3, delay: float=1.0, backoff: str='exponential') -> Any:
        if name in self._completed:
            log_event('step_skipped_idempotent', workflow=self.workflow_id, step=name)
            return self._completed[name]
        last_error = None
        current_delay = delay
        for attempt in range(1, retries + 1):
            try:
                log_event('step_executing', workflow=self.workflow_id, step=name, attempt=attempt)
                result = await fn()
                self._completed[name] = result
                if self._store:
                    self._store.save_step_result(self.workflow_id, name, result)
                log_event('step_completed', workflow=self.workflow_id, step=name)
                return result
            except Exception as e:
                last_error = e
                log_event('step_failed', workflow=self.workflow_id, step=name, attempt=attempt, error=str(e))
                if attempt < retries:
                    await asyncio.sleep(current_delay)
                    if backoff == 'exponential':
                        current_delay *= 2
        raise last_error

    async def wait_for_event(self, event_name: str, timeout: Optional[float]=None) -> Any:
        log_event('step_waiting_event', workflow=self.workflow_id, event=event_name)
        return await self._event_bus.wait_for_event(event_name, timeout)

    async def wait_for_approval(self, timeout: Optional[float]=None) -> Dict[str, Any]:
        log_event('step_waiting_approval', workflow=self.workflow_id)
        return await self._event_bus.wait_for_approval(self.workflow_id, timeout)

    async def update_agent_state(self, state: Dict[str, Any]):
        if self._agent_state_cb:
            self._agent_state_cb(state, replace=True)
            log_event('step_agent_state_updated', workflow=self.workflow_id)

    async def merge_agent_state(self, partial: Dict[str, Any]):
        if self._agent_state_cb:
            self._agent_state_cb(partial, replace=False)
            log_event('step_agent_state_merged', workflow=self.workflow_id)

    async def report_progress(self, progress: Dict[str, Any]):
        if self._progress_cb:
            await self._progress_cb(progress)
            log_event('step_progress_reported', workflow=self.workflow_id, progress=str(progress))