from fastapi import FastAPI
from app.api.router import api_router


app = FastAPI(
    title="fastapi-template",
    version="1.0.0",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"status": "ok"}
