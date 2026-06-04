from fastapi import APIRouter
from app.api.v1 import health_router


api_router = APIRouter()
api_router.include_router(health_router)
