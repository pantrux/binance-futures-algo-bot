import asyncio
import json
import logging
import traceback
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from apps.api.app.api.routes import router
from apps.api.app.core.settings import settings
from apps.api.app.observability.metrics import api_metrics

logger = logging.getLogger("apps.api.observability")


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0")

    @app.middleware("http")
    async def request_observability_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid4())
        start = perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:  # noqa: BLE001
            status_code = 500
            response = JSONResponse({"detail": "Internal Server Error"}, status_code=500)
            logger.error(
                json.dumps(
                    {
                        "event": "unhandled_request_error",
                        "request_id": request_id,
                        "path": request.url.path,
                        "method": request.method,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "traceback": traceback.format_exc(),
                    },
                    ensure_ascii=False,
                )
            )
        finally:
            duration_ms = (perf_counter() - start) * 1000.0
            try:
                await asyncio.to_thread(
                    api_metrics.record,
                    method=request.method,
                    path=request.url.path,
                    status_code=status_code,
                    latency_ms=duration_ms,
                )
            except Exception:  # noqa: BLE001
                pass
            logger.info(
                json.dumps(
                    {
                        "event": "api_request",
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": status_code,
                        "duration_ms": round(duration_ms, 4),
                    },
                    ensure_ascii=False,
                )
            )

        response.headers["x-request-id"] = request_id
        return response

    app.include_router(router)
    return app


app = create_app()
