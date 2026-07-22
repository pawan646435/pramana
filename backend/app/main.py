from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(title=settings.app_name)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}


# Phase 1 will register:
# app.include_router(chart_router, prefix="/api/charts")
# app.include_router(generation_router, prefix="/api/generate")
# app.include_router(eval_router, prefix="/api/eval")
