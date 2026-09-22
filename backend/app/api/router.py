from fastapi import APIRouter

from app.api.routes import clients, health, matches, providers, waitlist_entries

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(providers.router)
api_router.include_router(clients.router)
api_router.include_router(matches.router)
api_router.include_router(waitlist_entries.router)