import asyncio
from typing import Any, Callable, Coroutine, Dict, Optional
from telemetry.logger import log_event
from .events import EventBus


class Step:
    """
    A durable step within a workflow.

    Inspired by Cloudflare Workflows' step model:
    - step.do(name, fn) — execute a function with retry + idempotency
    - step.wait_for_event(name) — pause for external signal
    - step.update_agent_state() — sync state back to the owning agent

    Completed steps are tracked so they won't re-execute on retry.
    """

    def __init__(
        self,
        workflow_id: str,
        event_bus: EventBus,
        completed_steps: Dict[str, Any],
        agent_state_callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
    ):
        self.workflow_id = workflow_id
        self._event_bus = event_bus
        self._completed: Dict[str, Any] = completed_steps
        self._agent_state_cb = agent_state_callback
        self._progress_cb = progress_callback

    async def do(
        self,
        name: str,
        fn: Callable[..., Coroutine],
        *,
        retries: int = 3,
        delay: float = 1.0,
        backoff: str = "exponential",
    ) -> Any:
        """
        Execute a durable step.

        If this step already completed (idempotency check), return the
        cached result. Otherwise run fn with configurable retries.

        Args:
            name: Unique step name within the workflow.
            fn: Async callable to execute.
            retries: Max retry attempts.
            delay: Initial delay between retries (seconds).
            backoff: "exponential" or "linear".

        Returns:
            The result of fn().

        Raises:
            The last exception if all retries are exhausted.
        """
        if name in self._completed:
            log_event(
                "step_skipped_idempotent",
                workflow=self.workflow_id,
                step=name,
            )
            return self._completed[name]

        last_error = None
        current_delay = delay

        for attempt in range(1, retries + 1):
            try:
                log_event(
                    "step_executing",
                    workflow=self.workflow_id,
                    step=name,
                    attempt=attempt,
                )
                result = await fn()
                self._completed[name] = result
                log_event(
                    "step_completed",
                    workflow=self.workflow_id,
                    step=name,
                )
                return result

            except Exception as e:
                last_error = e
                log_event(
                    "step_failed",
                    workflow=self.workflow_id,
                    step=name,
                    attempt=attempt,
                    error=str(e),
                )
                if attempt < retries:
                    await asyncio.sleep(current_delay)
                    if backoff == "exponential":
                        current_delay *= 2
                    # linear: current_delay stays the same

        raise last_error

    async def wait_for_event(
        self, event_name: str, timeout: Optional[float] = None
    ) -> Any:
        """Pause this workflow step until an external event arrives."""
        log_event(
            "step_waiting_event",
            workflow=self.workflow_id,
            event=event_name,
        )
        return await self._event_bus.wait_for_event(event_name, timeout)

    async def wait_for_approval(
        self, timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Pause until the workflow is approved or rejected."""
        log_event(
            "step_waiting_approval",
            workflow=self.workflow_id,
        )
        return await self._event_bus.wait_for_approval(
            self.workflow_id, timeout
        )

    async def update_agent_state(self, state: Dict[str, Any]):
        """Replace the owning agent's state (durable)."""
        if self._agent_state_cb:
            self._agent_state_cb(state, replace=True)
            log_event(
                "step_agent_state_updated",
                workflow=self.workflow_id,
            )

    async def merge_agent_state(self, partial: Dict[str, Any]):
        """Merge into the owning agent's state (durable)."""
        if self._agent_state_cb:
            self._agent_state_cb(partial, replace=False)
            log_event(
                "step_agent_state_merged",
                workflow=self.workflow_id,
            )

    async def report_progress(self, progress: Dict[str, Any]):
        """Send a progress update to the owning agent."""
        if self._progress_cb:
            await self._progress_cb(progress)
            log_event(
                "step_progress_reported",
                workflow=self.workflow_id,
                progress=str(progress),
            )
