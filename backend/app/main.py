from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes.chart import router as chart_router
from app.api.routes.generate import router as generate_router
from app.api.routes.eval import router as eval_router
from app.api.routes.history import router as history_router

app = FastAPI(title=settings.app_name)

# The frontend runs on a different origin (Next.js dev server / deployed
# domain) than this API, so browser requests need CORS enabled - without
# it, every fetch from lib/api.ts fails the preflight check.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chart_router, prefix="/api/charts", tags=["charts"])
app.include_router(generate_router, prefix="/api/generate", tags=["generate"])
app.include_router(eval_router, prefix="/api/eval", tags=["eval"])
app.include_router(history_router, prefix="/api/history", tags=["history"])


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}
