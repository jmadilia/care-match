from fastapi import APIRouter

from app.api.routes import clients, health, providers

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(providers.router)
api_router.include_router(clients.router)