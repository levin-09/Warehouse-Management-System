"""
api.py — Application assembly (composition root).

Constructs the FastAPI instance and wires everything attached to it: the
startup/shutdown lifespan (database + scheduler), security-header middleware,
CORS, router registration, operational endpoints, and the OpenAPI schema.
Importing ``app`` from here yields a fully configured application, which is
what both :mod:`main` and any ASGI server target.

Structure:
    1. Lifespan (startup/shutdown resources)
    2. Application instance
    3. Security-header middleware
    4. CORS policy
    5. Router registration
    6. Operational endpoints (``/``, ``/health``, ``/ready``)
    7. OpenAPI schema customisation

Note:
    Business logic never appears here. This module composes; the routers it
    registers delegate to controllers, which own the rules, and controllers
    delegate persistence to CRUDs/services.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from core import logger
from core.apis.routes.auth_router import auth_router
from core.apis.routes.audit_router import audit_router
from core.apis.routes.bin_location_router import bin_location_router
from core.apis.routes.chatbot_router import chatbot_router
from core.apis.routes.damage_router import damage_router
from core.apis.routes.dashboard_router import dashboard_router
from core.apis.routes.inventory_router import inventory_router
from core.apis.routes.invoice_router import invoice_router
from core.apis.routes.notification_router import notification_router
from core.apis.routes.order_router import order_router
from core.apis.routes.product_router import product_router
from core.apis.routes.return_router import return_router
from core.apis.routes.seller_router import seller_router
from core.apis.routes.shipment_router import shipment_router
from core.apis.routes.user_router import user_router
from core.apis.routes.warehouse_router import warehouse_router
from core.config import settings
from core.database import database
from core.database.init_db import create_indexes, seed_default_data
from core.jobs.scheduler import shutdown_scheduler, start_scheduler

logging = logger(__name__)

# --------------------------------------------------------------------------- #
# 1. Lifespan
# --------------------------------------------------------------------------- #
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown resources.

    On startup: connect to MongoDB, verify/create indexes, seed default records,
    and start the scheduler. On shutdown: stop the scheduler and close the
    database client.

    Args:
        app: The FastAPI application.

    Yields:
        None

    Note:
        Resource teardown is guaranteed even if the application crashes, because
        the ``yield`` is the last statement before cleanup.
    """
    logging.info("Starting Whitfield WMS application")
    await database.connect()
    await create_indexes()
    await seed_default_data()
    if settings.enable_scheduler:
        start_scheduler()
    yield
    if settings.enable_scheduler:
        shutdown_scheduler()
    await database.close()
    logging.info("Application shutdown complete")


# --------------------------------------------------------------------------- #
# 2. Application instance
# --------------------------------------------------------------------------- #
#: The ASGI application. Referenced as ``core.apis.api:app`` by the server.
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Warehouse Management System backend for Whitfield Fulfillment. "
        "Routes, controllers, CRUDs, and services follow the Eigi backend standards."
    ),
    lifespan=lifespan,
    redoc_url="/documentation",
)


# --------------------------------------------------------------------------- #
# 3. Security-header middleware
# --------------------------------------------------------------------------- #
@app.middleware("http")
async def add_security_headers(request, call_next):
    """
    Attach hardening headers to every outbound response.

    Middleware wraps the entire request cycle, so these headers are applied
    uniformly — including on error responses, which are easy to miss when
    headers are set per route.

    Args:
        request: The incoming request.
        call_next: Continuation that dispatches to the next middleware or the
            matched route and returns its response.

    Returns:
        starlette.responses.Response: The downstream response with security
        headers added.

    Note:
        Headers applied and the attack each addresses:

        * ``X-Frame-Options: DENY`` — refuses framing by another origin,
          defeating clickjacking.
        * ``X-Content-Type-Options: nosniff`` — stops the browser from
          second-guessing a declared content type, which can otherwise turn an
          uploaded file into executable script.
        * ``X-XSS-Protection`` — legacy filter toggle, retained for old
          browsers; superseded by Content-Security-Policy.
        * ``Strict-Transport-Security`` — pins the origin to HTTPS for a year,
          closing the window in which an initial plaintext request could be
          intercepted.
        * ``Permissions-Policy`` — withholds geolocation and microphone access.
        * ``Cache-Control: no-store`` — keeps authenticated responses out of
          browser and proxy caches, where a later user could retrieve them.
    """
    # Dispatch first — headers are applied to the response on its way out.
    response = await call_next(request)

    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
    response.headers["Cache-Control"] = "no-store"

    return response


# --------------------------------------------------------------------------- #
# 4. CORS policy
# --------------------------------------------------------------------------- #
#: Origins permitted to call this API from a browser.
#:
#: ``"*"`` allows every origin, which is convenient for local work and too
#: permissive for a deployment. Replace it with an explicit list, e.g.
#: ``["https://app.example.com"]``.
#:
#: Note that ``"*"`` combined with ``allow_credentials=True`` is rejected by
#: browsers, so credentialed cross-origin requests will not succeed under this
#: configuration regardless.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# 5. Router registration
# --------------------------------------------------------------------------- #
# Each router declares its own ``APIRouter`` prefix and tags.
ROUTERS = [
    auth_router,
    user_router,
    warehouse_router,
    chatbot_router,
    seller_router,
    product_router,
    inventory_router,
    shipment_router,
    order_router,
    audit_router,
    damage_router,
    bin_location_router,
    return_router,
    invoice_router,
    notification_router,
    dashboard_router,
]

for router in ROUTERS:
    app.include_router(router)


# --------------------------------------------------------------------------- #
# 6. Operational endpoints
# --------------------------------------------------------------------------- #
@app.get("/")
def root():
    """
    Return a greeting confirming the application is serving.

    Returns:
        dict: ``{"message": str}``.
    """
    return {"message": f"Welcome to the {settings.app_name}!"}


@app.get("/health")
def health_check():
    """
    Report process liveness.

    Consumed by load balancers, container orchestrators, and uptime monitors,
    which restart or drain an instance that stops answering.

    Returns:
        dict: ``{"status": "healthy"}``.

    Note:
        This is a liveness check only — it reports that the process is running,
        not that its dependencies are reachable. See :func:`ready_check` for a
        readiness probe that also verifies MongoDB connectivity.
    """
    return {"status": "healthy"}


@app.get("/ready")
async def ready_check():
    """
    Report readiness, including database reachability.

    This is a readiness check: an instance that cannot reach MongoDB is
    reported as not ready so orchestrators take it out of rotation rather than
    serve traffic it will fail.

    Returns:
        dict: ``{"status": "ready"}`` if MongoDB is reachable.

    Raises:
        HTTPException 503: If MongoDB is not reachable.
    """
    from fastapi import HTTPException, status

    if not await database.ping():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unreachable")
    return {"status": "ready"}


# --------------------------------------------------------------------------- #
# 7. OpenAPI schema customisation
# --------------------------------------------------------------------------- #
def custom_openapi():
    """
    Build and cache the OpenAPI schema.

    Returns:
        dict: The OpenAPI document backing ``/docs`` and ``/documentation``.

    Note:
        The schema is generated once and stored on ``app.openapi_schema``;
        later calls return the cached document instead of walking every route
        again.

        Assigned to ``app.openapi`` below, replacing FastAPI's default
        generator. This is also the hook for adding shared metadata — security
        schemes, servers, tags — that cannot be expressed on individual routes.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.app_name,
        version="1.0.0",
        description="Warehouse Management System backend for Whitfield Fulfillment.",
        routes=app.routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
