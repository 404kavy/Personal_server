from fastapi import APIRouter
from app.api.v1.endpoints import events, rules

api_router = APIRouter()
api_router.include_router(events.router)
api_router.include_router(rules.router)
