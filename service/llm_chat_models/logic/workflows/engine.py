import uuid
import asyncio
from typing import Any, Callable, Coroutine, Dict, List, Optional
from datetime import datetime
from telemetry.logger import log_event
from logic.persistence.mongo_store import MongoWorkflowStore
from .status import WorkflowStatus, WorkflowResult
from .step import Step
from .events import EventBus

class WorkflowEngine:

    def __init__(self, store: Optional[MongoWorkflowStore]=None):
        self._store = store or MongoWorkflowStore()
        self._event_bus = EventBus(self._store)
        self._tasks: Dict[str, asyncio.Task] = {}
        log_event('workflow_engine_init', storage='mongodb')

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    async def run(self, name: str, workflow_fn: Callable[[Step], Coroutine], *, workflow_id: Optional[str]=None, metadata: Optional[Dict[str, Any]]=None, agent_state_callback: Optional[Callable]=None, progress_callback: Optional[Callable]=None) -> WorkflowResult:
        wf_id = workflow_id or f'wf-{uuid.uuid4().hex[:12]}'
        result = WorkflowResult(workflow_id=wf_id, status=WorkflowStatus.RUNNING, started_at=datetime.utcnow(), metadata={'name': name, **(metadata or {})})
        self._store.save_workflow(result.to_dict())
        log_event('workflow_started', workflow_id=wf_id, name=name)
        completed_steps = self._store.get_completed_steps(wf_id)
        step = Step(workflow_id=wf_id, event_bus=self._event_bus, completed_steps=completed_steps, store=self._store, agent_state_callback=agent_state_callback, progress_callback=progress_callback)
        try:
            output = await workflow_fn(step)
            result.status = WorkflowStatus.COMPLETED
            result.output = output
            result.completed_at = datetime.utcnow()
            result.steps_completed = len(completed_steps)
            log_event('workflow_completed', workflow_id=wf_id)
        except asyncio.CancelledError:
            result.status = WorkflowStatus.CANCELLED
            result.completed_at = datetime.utcnow()
            log_event('workflow_cancelled', workflow_id=wf_id)
        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.utcnow()
            log_event('workflow_failed', workflow_id=wf_id, error=str(e))
        self._store.save_workflow(result.to_dict())
        return result

    async def run_background(self, name: str, workflow_fn: Callable[[Step], Coroutine], **kwargs) -> str:
        wf_id = kwargs.pop('workflow_id', None) or f'wf-{uuid.uuid4().hex[:12]}'
        kwargs['workflow_id'] = wf_id
        task = asyncio.create_task(self.run(name, workflow_fn, **kwargs))
        self._tasks[wf_id] = task
        log_event('workflow_background_started', workflow_id=wf_id)
        return wf_id

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowResult]:
        doc = self._store.get_workflow(workflow_id)
        if not doc:
            return None
        return WorkflowResult(workflow_id=doc.get('workflow_id', workflow_id), status=WorkflowStatus(doc.get('status', 'pending')), output=doc.get('output'), error=doc.get('error'), steps_completed=doc.get('steps_completed', 0), steps_total=doc.get('steps_total', 0), metadata=doc.get('metadata', {}))

    def list_workflows(self, status: Optional[WorkflowStatus]=None) -> List[WorkflowResult]:
        status_str = status.value if status else None
        docs = self._store.list_workflows(status=status_str)
        results = []
        for doc in docs:
            results.append(WorkflowResult(workflow_id=doc.get('workflow_id', ''), status=WorkflowStatus(doc.get('status', 'pending')), output=doc.get('output'), error=doc.get('error'), steps_completed=doc.get('steps_completed', 0), steps_total=doc.get('steps_total', 0), metadata=doc.get('metadata', {})))
        return results

    async def cancel(self, workflow_id: str) -> bool:
        task = self._tasks.get(workflow_id)
        if task and (not task.done()):
            task.cancel()
            self._store.update_workflow_status(workflow_id, WorkflowStatus.CANCELLED.value)
            log_event('workflow_cancel_requested', workflow_id=workflow_id)
            return True
        return False

    async def approve(self, workflow_id: str, payload: Any=None):
        await self._event_bus.approve(workflow_id, payload)
        self._store.update_workflow_status(workflow_id, WorkflowStatus.RUNNING.value)

    async def reject(self, workflow_id: str, reason: str=''):
        await self._event_bus.reject(workflow_id, reason)

    async def send_event(self, workflow_id: str, event_name: str, payload: Any=None):
        await self._event_bus.send_event(event_name, payload)

    async def drain(self, timeout: float=10.0):
        active = [t for t in self._tasks.values() if not t.done()]
        if active:
            log_event('workflow_drain_start', count=len(active))
            done, pending = await asyncio.wait(active, timeout=timeout)
            for t in pending:
                t.cancel()
            log_event('workflow_drain_complete', completed=len(done), cancelled=len(pending))

    def close(self):
        self._store.close()