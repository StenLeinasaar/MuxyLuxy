"""Prometheus metrics for Ansible Roller (control plane + run worker)."""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.requests import Request
from starlette.responses import Response

RUNS_TOTAL = Counter(
    "ansible_roller_runs_total",
    "Ansible playbook runs that reached a terminal status",
    ("status",),
)

ACTIVE_RUNS = Gauge(
    "ansible_roller_active_runs",
    "Runs currently executing ansible-playbook in the background worker",
)

RUN_DURATION_SECONDS = Histogram(
    "ansible_roller_run_duration_seconds",
    "Wall-clock duration of a background run from in_progress through completion",
    buckets=(0.5, 1, 2, 5, 10, 30, 60, 120, 300, 600, 1800, 3600),
)

API_REQUESTS_TOTAL = Counter(
    "ansible_roller_api_requests_total",
    "HTTP requests served by the API process",
    ("method", "path"),
)


def configure_metrics(app: FastAPI) -> None:
    """Register /metrics and request-count middleware."""

    @app.middleware("http")
    async def _count_api_requests(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        try:
            return await call_next(request)
        finally:
            API_REQUESTS_TOTAL.labels(
                method=request.method,
                path=request.url.path,
            ).inc()

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        data = generate_latest()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)
