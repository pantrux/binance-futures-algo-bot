from fastapi import FastAPI

from apps.api.app.api.routes import router
from apps.api.app.core.settings import settings

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(router)
