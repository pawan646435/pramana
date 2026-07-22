from fastapi import FastAPI

from app.core.config import settings
from app.api.routes.chart import router as chart_router
from app.api.routes.generate import router as generate_router
from app.api.routes.eval import router as eval_router

app = FastAPI(title=settings.app_name)
app.include_router(chart_router, prefix="/api/charts", tags=["charts"])
app.include_router(generate_router, prefix="/api/generate", tags=["generate"])
app.include_router(eval_router, prefix="/api/eval", tags=["eval"])


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}
