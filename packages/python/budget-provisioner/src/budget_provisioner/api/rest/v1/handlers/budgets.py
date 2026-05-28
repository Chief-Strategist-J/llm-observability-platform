from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel
from typing import List
from opentelemetry import trace
from budget_provisioner.features.budget_management.index import BudgetNotFoundError
from budget_provisioner.shared.errors.codes import not_found, bad_request
from budget_provisioner.infra.auth import security

tracer = trace.get_tracer("budget-provisioner")
router = APIRouter()

class BudgetConfigUpsertRequest(BaseModel):
    max_budget: float
    window_size_secs: int = 900
    initial_fill_fraction: float = 0.1

class BudgetConfigResponse(BaseModel):
    user_id: str
    model: str
    max_budget: float
    window_size_secs: int
    initial_fill_fraction: float
    created_at: str
    updated_at: str

class BudgetStatusResponse(BaseModel):
    user_id: str
    model: str
    tokens_remaining: float
    burn_rate: float

def get_service(request: Request):
    return request.app.state.container.budget_service

def get_authenticator(request: Request):
    return request.app.state.container.authenticator

@router.post(
    "/budgets/{user_id}/{model}",
    response_model=BudgetConfigResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_or_update_budget(
    user_id: str,
    model: str,
    payload: BudgetConfigUpsertRequest,
    request: Request,
    response: Response,
    credentials=Depends(security),
    service=Depends(get_service),
    auth=Depends(get_authenticator)
):
    with tracer.start_as_current_span(
        "budget_handler.create_or_update_budget",
        attributes={
            "http.route": "/budgets/{user_id}/{model}",
            "http.method": "POST",
            "budget.user_id": user_id,
            "budget.model": model
        }
    ) as span:
        try:
            auth_data = auth.authenticate(credentials)
            existing = service.get_budget(user_id, model)
            
            config = service.create_or_update_budget(
                user_id=user_id,
                model=model,
                max_budget=payload.max_budget,
                window_size_secs=payload.window_size_secs,
                initial_fill_fraction=payload.initial_fill_fraction
            )
            
            if existing:
                response.status_code = status.HTTP_200_OK
                
            return BudgetConfigResponse(
                user_id=config.user_id,
                model=config.model,
                max_budget=config.max_budget,
                window_size_secs=config.window_size_secs,
                initial_fill_fraction=config.initial_fill_fraction,
                created_at=config.created_at.isoformat(),
                updated_at=config.updated_at.isoformat()
            )
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            raise

@router.get(
    "/budgets/{user_id}",
    response_model=dict
)
async def list_budgets(
    user_id: str,
    credentials=Depends(security),
    service=Depends(get_service),
    auth=Depends(get_authenticator)
):
    with tracer.start_as_current_span(
        "budget_handler.list_budgets",
        attributes={
            "http.route": "/budgets/{user_id}",
            "http.method": "GET",
            "budget.user_id": user_id
        }
    ) as span:
        try:
            auth_data = auth.authenticate(credentials)
            configs = service.list_budgets(user_id)
            return {
                "budgets": [
                    BudgetConfigResponse(
                        user_id=c.user_id,
                        model=c.model,
                        max_budget=c.max_budget,
                        window_size_secs=c.window_size_secs,
                        initial_fill_fraction=c.initial_fill_fraction,
                        created_at=c.created_at.isoformat(),
                        updated_at=c.updated_at.isoformat()
                    )
                    for c in configs
                ]
            }
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            raise

@router.delete(
    "/budgets/{user_id}/{model}",
    status_code=status.HTTP_200_OK
)
async def delete_budget(
    user_id: str,
    model: str,
    credentials=Depends(security),
    service=Depends(get_service),
    auth=Depends(get_authenticator)
):
    with tracer.start_as_current_span(
        "budget_handler.delete_budget",
        attributes={
            "http.route": "/budgets/{user_id}/{model}",
            "http.method": "DELETE",
            "budget.user_id": user_id,
            "budget.model": model
        }
    ) as span:
        try:
            auth_data = auth.authenticate(credentials)
            deleted = service.delete_budget(user_id, model)
            if not deleted:
                raise not_found("Budget config not found")
            return {"success": True, "message": "Budget deleted successfully"}
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            raise

@router.get(
    "/budgets/{user_id}/{model}/status",
    response_model=BudgetStatusResponse
)
async def get_budget_status(
    user_id: str,
    model: str,
    credentials=Depends(security),
    service=Depends(get_service),
    auth=Depends(get_authenticator)
):
    with tracer.start_as_current_span(
        "budget_handler.get_budget_status",
        attributes={
            "http.route": "/budgets/{user_id}/{model}/status",
            "http.method": "GET",
            "budget.user_id": user_id,
            "budget.model": model
        }
    ) as span:
        try:
            auth_data = auth.authenticate(credentials)
            try:
                status_info = service.get_budget_status(user_id, model)
                return BudgetStatusResponse(
                    user_id=status_info.user_id,
                    model=status_info.model,
                    tokens_remaining=status_info.tokens_remaining,
                    burn_rate=status_info.burn_rate
                )
            except BudgetNotFoundError as exc:
                raise not_found(str(exc)) from exc
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            raise
