from fastapi import APIRouter, Depends

from app.api.routes import (
    clients,
    comparisons,
    health,
    intake,
    matches,
    providers,
    simulation_runs,
    waitlist_entries,
)
from app.api.security import admin_key_dependency
from app.core.config import settings


def build_api_router(*, admin_enabled: bool, admin_key: str | None) -> APIRouter:
    """The public routes are always mounted. The CRUD and strategy-run routers are mounted
    only when the admin API is enabled, behind an optional X-Admin-Key check."""
    router = APIRouter()
    router.include_router(health.router)
    router.include_router(comparisons.router)
    router.include_router(intake.router)

    if admin_enabled:
        admin = [Depends(admin_key_dependency(admin_key))]
        for module in (providers, clients, matches, waitlist_entries, simulation_runs):
            router.include_router(module.router, dependencies=admin)
    return router


api_router = build_api_router(
    admin_enabled=settings.admin_api_enabled, admin_key=settings.ADMIN_API_KEY
)
