from fastapi import APIRouter

from app.api.routes import (
    advisor,
    agent_lab,
    auth,
    budgets,
    decisions,
    evaluation,
    expenses,
    goals,
    health,
    hitl,
    monitoring,
    profile,
    rag,
    salary,
    scenarios,
    transactions,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
api_router.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
api_router.include_router(salary.router, prefix="/salary", tags=["salary"])
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
api_router.include_router(advisor.router, prefix="/advisor", tags=["advisor"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(decisions.router, tags=["decisions"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(hitl.router, prefix="/hitl", tags=["hitl"])
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["evaluation"])
api_router.include_router(agent_lab.router, prefix="/agent-lab", tags=["agent-lab"])
