from fastapi import APIRouter, HTTPException
from typing import List, Optional
from gateway.schemas.workflows import (
    WorkflowRunRequest,
    WorkflowActionRequest,
    WorkflowEventRequest,
    WorkflowResponse,
    WorkflowListResponse,
)
from logic.workflows.engine import WorkflowEngine
from logic.workflows.status import WorkflowStatus
from telemetry.logger import log_event, get_tracer, trace_with_details

router = APIRouter(prefix="/workflows", tags=["workflows"])

_engine: Optional[WorkflowEngine] = None


def get_engine() -> WorkflowEngine:
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine


@router.get("", response_model=WorkflowListResponse)
@trace_with_details(get_tracer())
async def list_workflows(status: Optional[str] = None):
    """List all workflows, optionally filtered by status."""
    log_event("api_list_workflows", status_filter=status)
    engine = get_engine()

    status_filter = None
    if status:
        try:
            status_filter = WorkflowStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: '{status}'. "
                f"Valid: {[s.value for s in WorkflowStatus]}",
            )

    results = engine.list_workflows(status=status_filter)
    return WorkflowListResponse(
        workflows=[
            WorkflowResponse(**r.to_dict()) for r in results
        ],
        total=len(results),
    )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
@trace_with_details(get_tracer())
async def get_workflow(workflow_id: str):
    """Get workflow status by ID."""
    log_event("api_get_workflow", workflow_id=workflow_id)
    engine = get_engine()
    result = engine.get_workflow(workflow_id)
    if not result:
        raise HTTPException(
            status_code=404, detail=f"Workflow {workflow_id} not found"
        )
    return WorkflowResponse(**result.to_dict())


@router.post("/{workflow_id}/approve")
@trace_with_details(get_tracer())
async def approve_workflow(
    workflow_id: str, request: WorkflowActionRequest
):
    """Approve a workflow waiting for approval."""
    log_event("api_approve_workflow", workflow_id=workflow_id)
    engine = get_engine()
    await engine.approve(workflow_id, payload=request.payload)
    return {"success": True, "message": f"Workflow {workflow_id} approved"}


@router.post("/{workflow_id}/reject")
@trace_with_details(get_tracer())
async def reject_workflow(
    workflow_id: str, request: WorkflowActionRequest
):
    """Reject a workflow waiting for approval."""
    log_event("api_reject_workflow", workflow_id=workflow_id)
    engine = get_engine()
    await engine.reject(workflow_id, reason=request.reason)
    return {"success": True, "message": f"Workflow {workflow_id} rejected"}


@router.post("/{workflow_id}/cancel")
@trace_with_details(get_tracer())
async def cancel_workflow(workflow_id: str):
    """Cancel a running workflow."""
    log_event("api_cancel_workflow", workflow_id=workflow_id)
    engine = get_engine()
    cancelled = await engine.cancel(workflow_id)
    if not cancelled:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow {workflow_id} cannot be cancelled "
            "(not running or not found)",
        )
    return {"success": True, "message": f"Workflow {workflow_id} cancelled"}


@router.post("/{workflow_id}/events")
@trace_with_details(get_tracer())
async def send_workflow_event(
    workflow_id: str, request: WorkflowEventRequest
):
    """Send a custom event to a running workflow."""
    log_event(
        "api_send_workflow_event",
        workflow_id=workflow_id,
        event=request.event_name,
    )
    engine = get_engine()
    await engine.send_event(
        workflow_id, request.event_name, request.payload
    )
    return {
        "success": True,
        "message": f"Event '{request.event_name}' sent to {workflow_id}",
    }
