from fastapi import APIRouter
from app.api.v1 import index_router


api_router = APIRouter()
api_router.include_router(index_router)
