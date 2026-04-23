"""Superset configuration for bi-stack.

Imported by Superset at process start via SUPERSET_CONFIG_PATH. Everything
that must change between local/prod is pulled from environment variables.
Never put raw secrets in this file — they come from Secret Manager (prod)
or the local `.env` via docker-compose.
"""

from __future__ import annotations

import os
from datetime import timedelta

from cachelib.redis import RedisCache


def _env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(f"Required env var {name} is not set")
    return value or ""


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
SECRET_KEY = _env("SUPERSET_SECRET_KEY", required=True)
SQLALCHEMY_DATABASE_URI = _env("SUPERSET_METADATA_DB_URI", required=True)

# Neon's direct endpoint supports normal pooling — use a modest pool; dashboards
# hit this DB for metadata only, not for analytics queries.
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 5,
    "max_overflow": 10,
    "pool_pre_ping": True,
    "pool_recycle": 300,
    # TCP keepalives keep Neon's proxy from dropping long-running transactions
    # silently (observed: SSL SYSCALL EOF mid-`superset init`).
    "connect_args": {
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
}

# ---------------------------------------------------------------------------
# Redis — cache + Celery broker + results backend
# ---------------------------------------------------------------------------
REDIS_URL = _env("REDIS_URL", "redis://redis:6379/0")

CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 60 * 60,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_URL": REDIS_URL,
}
DATA_CACHE_CONFIG = {**CACHE_CONFIG, "CACHE_KEY_PREFIX": "superset_data_"}
FILTER_STATE_CACHE_CONFIG = {**CACHE_CONFIG, "CACHE_KEY_PREFIX": "superset_filter_"}
EXPLORE_FORM_DATA_CACHE_CONFIG = {**CACHE_CONFIG, "CACHE_KEY_PREFIX": "superset_explore_"}

RESULTS_BACKEND = RedisCache(
    host=REDIS_URL.replace("redis://", "").split(":")[0],
    port=int(REDIS_URL.rsplit(":", 1)[-1].split("/")[0]) if ":" in REDIS_URL else 6379,
    key_prefix="superset_results",
)


class CeleryConfig:
    broker_url = REDIS_URL
    result_backend = REDIS_URL
    worker_prefetch_multiplier = 1
    task_acks_late = True
    imports = ("superset.sql_lab", "superset.tasks.scheduler")
    beat_schedule = {
        "reports.scheduler": {
            "task": "reports.scheduler",
            "schedule": timedelta(minutes=1),
        },
        "reports.prune_log": {
            "task": "reports.prune_log",
            "schedule": timedelta(days=1),
        },
    }


CELERY_CONFIG = CeleryConfig

# ---------------------------------------------------------------------------
# Feature flags
# ---------------------------------------------------------------------------
FEATURE_FLAGS = {
    "DASHBOARD_RBAC": True,
    "EMBEDDED_SUPERSET": True,
    "ALERT_REPORTS": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "HORIZONTAL_FILTER_BAR": True,
}

# ---------------------------------------------------------------------------
# Embedded dashboards — guest token config
# biz-demos mints these server-side after validating a demo code against its
# Cloudflare KV `DEMO_CODES` namespace. See docs/runbook.md for rotation.
# ---------------------------------------------------------------------------
GUEST_ROLE_NAME = "Public"
GUEST_TOKEN_JWT_SECRET = _env("GUEST_TOKEN_JWT_SECRET", SECRET_KEY)
GUEST_TOKEN_JWT_ALGO = "HS256"
GUEST_TOKEN_JWT_EXP_SECONDS = 60 * 60  # 1 hour

# ---------------------------------------------------------------------------
# Region / branding
# ---------------------------------------------------------------------------
APP_NAME = "2nth.ai BI"
BABEL_DEFAULT_LOCALE = "en"
LANGUAGES = {"en": {"flag": "us", "name": "English"}}
DEFAULT_FEATURE_FLAGS_TIMEZONE = "Africa/Johannesburg"
MAPBOX_API_KEY = _env("MAPBOX_API_KEY", "")

# ---------------------------------------------------------------------------
# Security headers & CORS — tightened for Cloudflare Pages embed
# ---------------------------------------------------------------------------
TALISMAN_ENABLED = False  # Cloudflare terminates TLS; avoid double-headers
ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "allow_headers": ["*"],
    "resources": ["*"],
    "origins": [
        "https://dev.biz-demos.pages.dev",
        "https://biz-demos.pages.dev",
        "https://demos.2nth.ai",
    ],
}

# POPIA: no PII exported to third-party services by default.
WEBDRIVER_BASEURL = _env("WEBDRIVER_BASEURL", "http://superset-web:8088/")
WEBDRIVER_BASEURL_USER_FRIENDLY = _env("WEBDRIVER_BASEURL_USER_FRIENDLY", "https://bi.2nth.ai/")
