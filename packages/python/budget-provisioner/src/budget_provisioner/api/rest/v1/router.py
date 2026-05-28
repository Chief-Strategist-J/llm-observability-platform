from fastapi import APIRouter
from budget_provisioner.api.rest.v1.handlers.budgets import router as budgets_router

router = APIRouter()
router.include_router(budgets_router)
