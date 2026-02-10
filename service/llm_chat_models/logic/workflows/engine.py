import uuid
import asyncio
from typing import Any, Callable, Coroutine, Dict, List, Optional
from datetime import datetime
from telemetry.logger import log_event
from .status import WorkflowStatus, WorkflowResult
from .step import Step
from .events import EventBus


class WorkflowEngine:
    """
    Durable workflow engine inspired by Cloudflare Workflows.

    Manages workflow lifecycle: run, pause, resume, cancel.
    Each workflow gets a Step context for durable step execution,
    and an EventBus for agent↔workflow communication.

    Usage:
        engine = WorkflowEngine()

        async def my_workflow(step: Step):
            data = await step.do("fetch", fetch_data)
            processed = await step.do("process", lambda: process(data))
            approval = await step.wait_for_approval(timeout=3600)
            if not approval["approved"]:
                raise ValueError("Workflow rejected")
            return processed

        result = await engine.run("data-pipeline", my_workflow)
    """

    def __init__(self):
        self._workflows: Dict[str, WorkflowResult] = {}
        self._event_bus = EventBus()
        self._completed_steps: Dict[str, Dict[str, Any]] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        log_event("workflow_engine_init")

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    async def run(
        self,
        name: str,
        workflow_fn: Callable[[Step], Coroutine],
        *,
        workflow_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        agent_state_callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
    ) -> WorkflowResult:
        """
        Execute a workflow function with durable step support.

        Args:
            name: Human-readable workflow name.
            workflow_fn: Async function(step: Step) -> Any.
            workflow_id: Optional ID (auto-generated if not provided).
            metadata: Arbitrary metadata to attach.
            agent_state_callback: Called when step.update_agent_state() fires.
            progress_callback: Called when step.report_progress() fires.

        Returns:
            WorkflowResult with status and output.
        """
        wf_id = workflow_id or f"wf-{uuid.uuid4().hex[:12]}"

        result = WorkflowResult(
            workflow_id=wf_id,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.utcnow(),
            metadata={"name": name, **(metadata or {})},
        )
        self._workflows[wf_id] = result
        self._completed_steps.setdefault(wf_id, {})

        log_event("workflow_started", workflow_id=wf_id, name=name)

        step = Step(
            workflow_id=wf_id,
            event_bus=self._event_bus,
            completed_steps=self._completed_steps[wf_id],
            agent_state_callback=agent_state_callback,
            progress_callback=progress_callback,
        )

        try:
            output = await workflow_fn(step)
            result.status = WorkflowStatus.COMPLETED
            result.output = output
            result.completed_at = datetime.utcnow()
            result.steps_completed = len(self._completed_steps[wf_id])
            log_event("workflow_completed", workflow_id=wf_id)

        except asyncio.CancelledError:
            result.status = WorkflowStatus.CANCELLED
            result.completed_at = datetime.utcnow()
            log_event("workflow_cancelled", workflow_id=wf_id)

        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.utcnow()
            log_event(
                "workflow_failed", workflow_id=wf_id, error=str(e)
            )

        return result

    async def run_background(
        self,
        name: str,
        workflow_fn: Callable[[Step], Coroutine],
        **kwargs,
    ) -> str:
        """
        Start a workflow as a background task. Returns the workflow ID.
        Use get_workflow() to check status.
        """
        wf_id = kwargs.pop("workflow_id", None) or f"wf-{uuid.uuid4().hex[:12]}"
        kwargs["workflow_id"] = wf_id

        task = asyncio.create_task(
            self.run(name, workflow_fn, **kwargs)
        )
        self._tasks[wf_id] = task
        log_event("workflow_background_started", workflow_id=wf_id)
        return wf_id

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowResult]:
        """Get the current result/status of a workflow."""
        return self._workflows.get(workflow_id)

    def list_workflows(
        self,
        status: Optional[WorkflowStatus] = None,
    ) -> List[WorkflowResult]:
        """List workflows, optionally filtered by status."""
        results = list(self._workflows.values())
        if status:
            results = [r for r in results if r.status == status]
        return results

    async def cancel(self, workflow_id: str) -> bool:
        """Cancel a running background workflow."""
        task = self._tasks.get(workflow_id)
        if task and not task.done():
            task.cancel()
            log_event("workflow_cancel_requested", workflow_id=workflow_id)
            return True
        return False

    async def approve(self, workflow_id: str, payload: Any = None):
        """Approve a workflow waiting for approval."""
        await self._event_bus.approve(workflow_id, payload)
        result = self._workflows.get(workflow_id)
        if result:
            result.status = WorkflowStatus.RUNNING

    async def reject(self, workflow_id: str, reason: str = ""):
        """Reject a workflow waiting for approval."""
        await self._event_bus.reject(workflow_id, reason)

    async def send_event(
        self, workflow_id: str, event_name: str, payload: Any = None
    ):
        """Send a custom event to a running workflow."""
        await self._event_bus.send_event(event_name, payload)
