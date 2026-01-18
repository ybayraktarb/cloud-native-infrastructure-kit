"""
Cloud-Native-Ops-Starter API

A production-grade reference architecture demonstrating modern cloud-native
software delivery lifecycle (SDLC) practices.
"""

import os
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

# Application metadata
APP_NAME = "Cloud-Native-Ops-Starter"
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_MAINTAINER = "Cloud-Native-Ops Team"
APP_DESCRIPTION = "Production-grade cloud-native reference architecture"

# Initialize FastAPI application
app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.get(
    "/",
    summary="Application Metadata",
    description="Returns application metadata including name, version, and maintainer information.",
    response_class=JSONResponse,
    tags=["Root"],
)
async def root() -> dict[str, str]:
    """
    Root endpoint returning application metadata.

    Returns:
        dict: Application metadata containing name, version, description, and maintainer.
    """
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
        "maintainer": APP_MAINTAINER,
    }


@app.get(
    "/health",
    summary="Health Check",
    description="Kubernetes liveness/readiness probe endpoint. Returns service health status.",
    response_class=JSONResponse,
    tags=["Health"],
)
async def health_check() -> dict[str, Any]:
    """
    Production-ready health check endpoint for Kubernetes probes.

    This endpoint is designed for:
    - Liveness probes: Verify the service is running
    - Readiness probes: Verify the service is ready to accept traffic

    Returns:
        dict: Health status with timestamp and version information.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": APP_VERSION,
        "checks": {
            "api": "operational",
        },
    }


@app.get(
    "/api/v1/system-status",
    summary="System Status",
    description="Returns detailed system status information for monitoring and diagnostics.",
    response_class=JSONResponse,
    tags=["API v1"],
)
async def system_status() -> dict[str, Any]:
    """
    System status endpoint providing operational metrics and service information.

    Simulates a real service by returning environment and runtime details.

    Returns:
        dict: Comprehensive system status information.
    """
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "region": os.getenv("AWS_REGION", "us-east-1"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": {
            "api_gateway": "operational",
            "database": "operational",
            "cache": "operational",
            "message_queue": "operational",
        },
        "metrics": {
            "uptime_seconds": 99999,
            "requests_total": 1234567,
            "error_rate_percent": 0.01,
            "avg_response_time_ms": 45,
        },
        "dependencies": {
            "postgres": {"status": "connected", "latency_ms": 2},
            "redis": {"status": "connected", "latency_ms": 1},
            "external_api": {"status": "reachable", "latency_ms": 120},
        },
    }


@app.get(
    "/ready",
    summary="Readiness Check",
    description="Kubernetes readiness probe endpoint. Indicates if the service is ready to receive traffic.",
    response_class=JSONResponse,
    status_code=status.HTTP_200_OK,
    tags=["Health"],
)
async def readiness_check() -> dict[str, str]:
    """
    Readiness probe endpoint for Kubernetes.

    Separate from liveness to allow for graceful startup and shutdown.
    In production, this would check database connections, cache availability, etc.

    Returns:
        dict: Readiness status.
    """
    return {"status": "ready"}


@app.get(
    "/live",
    summary="Liveness Check",
    description="Kubernetes liveness probe endpoint. Indicates if the service is alive.",
    response_class=JSONResponse,
    status_code=status.HTTP_200_OK,
    tags=["Health"],
)
async def liveness_check() -> dict[str, str]:
    """
    Liveness probe endpoint for Kubernetes.

    Minimal check to verify the process is running and responsive.

    Returns:
        dict: Liveness status.
    """
    return {"status": "alive"}
    