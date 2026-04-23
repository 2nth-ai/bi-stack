# bi-stack

**Apache Superset + dbt + Neon Postgres** — the BI stack behind 2nth.ai demos.

- **Proposition**: the lowest-risk entry point to AI transformation — Superset over a read-only warehouse, seeded by dbt, deployed on Cloudflare/Google edge, with Workers AI NL→SQL as the next layer.
- **Live pitch**: [dev.biz-demos.pages.dev/bi/](https://dev.biz-demos.pages.dev/bi/)
- **Explainers**:
  - [Apache Superset](https://dev.know-2nth.pages.dev/explainers/data/analytics/superset)
  - [PostgreSQL for analytics](https://dev.know-2nth.pages.dev/explainers/data/warehousing/postgresql)

## v1 scope

- Superset 4.x running on Google Cloud Run in `africa-south1`.
- Neon Postgres (paid, `imbilawork@gmail.com`) in `aws-eu-central-1` — both Superset metadata and the analytics warehouse in one project, two schemas, two branches (`main`, `dev`).
- dbt-core scheduled as a Cloud Run Job (02:00 SAST daily) seeding synthetic **SilverGro agri/commodities** data — SAFEX prices, client book, feedlot rations, hedge coverage.
- Redis via Upstash (cache + Celery broker).
- GitHub Actions → Artifact Registry → Cloud Run via Workload Identity Federation.

ClickHouse and Workers AI NL→SQL are **v2** — see `docs/architecture.md`.

## Repo layout

```
bi-stack/
  docker-compose.yml        # local dev stack
  .env.example              # Neon + Redis + Superset env
  superset/                 # Dockerfile, config, bootstrap
  dbt/                      # dbt project + SilverGro seeds + models
  gcp/                      # Cloud Run deploy scripts
  .github/workflows/        # CI + tag-triggered deploy
  docs/                     # architecture, runbook
```

## Local dev

Full clone-to-running-stack walkthrough: **[docs/quickstart.md](docs/quickstart.md)**.

Short version:

```bash
./scripts/setup-env.sh               # derives .env from a Neon pooled URI
# paste sql/neon-init.sql into Neon SQL Editor (one-time)
docker compose up --build
# http://localhost:8088 — login with admin / ADMIN_PASSWORD from .env
```

Run dbt against the Neon dev branch:

```bash
cd dbt
cp profiles.yml.tmpl ~/.dbt/profiles.yml    # then edit target URIs
dbt deps
dbt seed
dbt build
```

## Deploy to Cloud Run

One-time bootstrap (Artifact Registry, Secret Manager, Workload Identity Federation, service accounts):

```bash
./gcp/secrets-bootstrap.sh
```

Then deploy the three Superset services + the dbt job + the scheduler:

```bash
./gcp/deploy-web.sh
./gcp/deploy-worker.sh
./gcp/deploy-beat.sh
./gcp/deploy-dbt-job.sh
./gcp/scheduler.sh
```

CI/CD: tag `v*` to trigger `.github/workflows/deploy.yml`.

## Top gotchas

1. **Cloud Run `--cpu-always-allocated` is mandatory** on the `worker` and `beat` services. Without it Celery silently stops between requests. Forces instance-based billing (~$15–25/mo per always-on service).
2. **Neon pooled endpoint breaks SQLAlchemy prepared statements.** Superset metadata uses the **direct** (unpooled) Neon endpoint; dbt uses the pooled endpoint.
3. **`superset_config.py` is baked into the image**, not mounted from Secret Manager. Secrets are env vars referenced by name inside the config.
4. **Guest-token signing key rotation invalidates every live embed.** 12-month key; rotation playbook in `docs/runbook.md`.
5. **Neon Frankfurt latency (~160 ms from africa-south1)** is acceptable because Redis caches query results; dbt runs feel slow but run overnight.

## License

MIT — see [LICENSE](LICENSE).
