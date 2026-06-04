from fastapi import FastAPI
from app.core import settings
from app.api.router import api_router


app = FastAPI(
    title="fastapi-template",
    version="1.0.0",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "status": "ok",
        "environment": settings.environment,
    }
