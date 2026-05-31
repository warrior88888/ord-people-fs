import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import Response
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from ord_people.config.settings import Settings
from ord_people.infra.logging import request_id_var, user_id_var

logger = logging.getLogger(__name__)


def register_middleware(app: FastAPI, settings: Settings) -> None:
    if settings.app.behind_proxy:
        app.add_middleware(
            ProxyHeadersMiddleware,
            trusted_hosts=settings.app.forwarded_allow_ips,
        )
        logger.debug(
            "proxy_headers_middleware_enabled trusted=%s",
            settings.app.forwarded_allow_ips,
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.app.allowed_hosts,
    )
    logger.debug(
        "cors_middleware_added origins=%s allowed_hosts=%s",
        settings.app.cors_origins,
        settings.app.allowed_hosts,
    )

    slow_ms = settings.log.slow_request_ms

    @app.middleware("http")
    async def _request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:12]
        rid_token = request_id_var.set(request_id)
        uid_token = user_id_var.set("-")
        path = request.url.path
        method = request.method
        ip = request.client.host if request.client else "-"
        logger.info("request_start method=%s path=%s ip=%s", method, path, ip)
        start = time.perf_counter()
        status_code = 500
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-Id"] = request_id
            return response
        except Exception:
            logger.exception(
                "request_unhandled method=%s path=%s",
                method,
                path,
            )
            raise
        finally:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            if elapsed_ms >= slow_ms:
                logger.warning(
                    "request_slow method=%s path=%s status=%d elapsed_ms=%d",
                    method,
                    path,
                    status_code,
                    elapsed_ms,
                )
            else:
                logger.info(
                    "request_end method=%s path=%s status=%d elapsed_ms=%d",
                    method,
                    path,
                    status_code,
                    elapsed_ms,
                )
            request_id_var.reset(rid_token)
            user_id_var.reset(uid_token)
