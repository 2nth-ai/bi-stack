# bi-stack architecture

## Moving parts

```
           ┌──────────────────────────┐      ┌─────────────────────────┐
           │  biz-demos (CF Pages)    │      │   Cloudflare Worker      │
           │  dev.biz-demos/bi/       │─────▶│   mints guest token      │
           │  iframe embed            │      │   (validates demo code)  │
           └──────────────┬───────────┘      └────────────┬────────────┘
                          │                                │
                          ▼                                ▼
                 ┌────────────────────────────────────────────┐
                 │   Cloud Run — africa-south1                │
                 │   ┌─────────────┐ ┌───────────┐ ┌────────┐ │
                 │   │ superset-web│ │ -worker   │ │ -beat  │ │
                 │   └──────┬──────┘ └─────┬─────┘ └────┬───┘ │
                 └──────────┼──────────────┼─────────────┼────┘
                            │              │             │
                            ▼              ▼             ▼
                        ┌────────────────────────┐  ┌──────────┐
                        │  Upstash Redis (TLS)   │  │  Neon    │
                        │  cache + Celery broker │  │  Postgres│
                        └────────────────────────┘  │  metadata│
                                                    │  +       │
                                                    │  warehouse│
                                                    └──────────┘
                                                          ▲
                                                          │
                 ┌────────────────────────────────────────┤
                 │  Cloud Run Job — bi-dbt-run             │
                 │  Cloud Scheduler cron 02:00 SAST daily  │
                 │  dbt build → analytics schema           │
                 └─────────────────────────────────────────┘
```

## Services

| Service                   | Cloud Run type | CPU mode             | Min | Max | Notes                           |
| ------------------------- | -------------- | -------------------- | --- | --- | ------------------------------- |
| `bi-superset-web`         | service        | request-allocated    | 1   | 4   | public; `--allow-unauthenticated` |
| `bi-superset-worker`      | service        | **always-allocated** | 1   | 2   | `--no-cpu-throttling`           |
| `bi-superset-beat`        | service        | **always-allocated** | 1   | 1   | singleton; `--no-cpu-throttling` |
| `bi-dbt-run`              | job            | n/a (task-scoped)    | —   | —   | scheduler-triggered             |

## Data

- **Neon project**: `bi-stack`, region `aws-eu-central-1`.
- **Branches**: `main` (prod), `dev` (local).
- **Schemas**: `superset_meta` (Superset tables), `analytics` (dbt models).
- **Endpoints used**:
  - Superset metadata → **direct/unpooled** (SQLAlchemy + prepared statements need this).
  - dbt → **pooled** (short-lived connections tolerate transaction pooling fine).

## Secrets (Google Secret Manager)

| Secret name                   | Consumers                         |
| ----------------------------- | --------------------------------- |
| `SUPERSET_METADATA_DB_URI`    | web, worker, beat                 |
| `ANALYTICS_DB_URI`            | web (registered as data source)   |
| `NEON_POOLED_URI`             | dbt job                           |
| `REDIS_URL`                   | web, worker, beat                 |
| `SUPERSET_SECRET_KEY`         | web, worker, beat                 |
| `GUEST_TOKEN_JWT_SECRET`      | web + the biz-demos Worker        |
| `ADMIN_PASSWORD`              | bootstrap only                    |
| `MAPBOX_API_KEY`              | web (geo charts)                  |

## Dataflow — daily refresh

1. **02:00 SAST** — Cloud Scheduler fires `bi-dbt-run` Job.
2. Job pulls dbt image, reads `NEON_POOLED_URI` from Secret Manager.
3. Runs `dbt deps && dbt build --target prod` against the Neon `main` branch.
4. Refreshes `analytics.*` views/tables: `stg_*`, `dim_client`, `fct_basis_margin`, `fct_hedge_coverage`, `fct_safex_daily`.
5. Superset dashboards pick up the new data on next cache miss (Redis TTL 1h).

## Embed flow

1. Visitor lands on `dev.biz-demos.pages.dev/bi/` with a demo code in the URL or form.
2. Cloudflare Worker validates the code against the `DEMO_CODES` KV namespace.
3. Worker POSTs to Superset's `/api/v1/security/guest_token/` with a short-lived JWT payload (resources + RLS filter).
4. Worker returns the guest token to the page; the iframe uses it to embed the dashboard.

Guest tokens expire hourly (see `GUEST_TOKEN_JWT_EXP_SECONDS` in `superset_config.py`). Signing key rotation is a **breaking change** for any open embeds — see `runbook.md`.

## v2 backlog

- **ClickHouse** as the analytics warehouse (keep Neon for Superset metadata).
- **Cloudflare Workers AI NL→SQL** — prompts translated to SQL via Llama / Workers AI, executed against the `analytics` schema through Superset's `/api/v1/sqllab/execute/`.
- **Terraform** once a second environment (staging) exists.
- **Per-client RLS** overlays on guest tokens — the guest-token JWT already supports `rls` claims; waiting on a real client to model against.
