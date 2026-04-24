# Quickstart — fresh MacBook

Clone-to-running-stack in ~10 minutes. Assumes macOS with Homebrew.

## Prerequisites

```bash
brew install --cask docker         # Docker Desktop
brew install gh git                # GitHub CLI + git (likely already there)
open -a Docker                     # start Docker Desktop, wait ~30s
```

Sign into GitHub if you haven't: `gh auth login` (choose HTTPS, browser).

## 1 — Clone

```bash
cd ~/Projects   # or wherever you keep repos
gh repo clone 2nth-ai/bi-stack
cd bi-stack
```

If PR #1 hasn't been merged yet, check it out:

```bash
gh pr checkout 1
```

## 2 — Get the Neon connection string

From the Neon dashboard (https://console.neon.tech, logged in as `imbilawork@gmail.com`):

- Project: **bi-stack**
- Connection Details → **Pooled** connection string → copy

Either save it as `secrets.txt` in the repo root (gitignored) **or** paste it when prompted in the next step.

## 3 — Generate `.env`

```bash
./scripts/setup-env.sh
```

This derives the direct endpoint from the pooled one, generates `SUPERSET_SECRET_KEY`, `GUEST_TOKEN_JWT_SECRET`, and `ADMIN_PASSWORD`, and writes a mode-600 `.env`. Print the admin password:

```bash
grep ADMIN_PASSWORD .env
```

## 4 — Create schemas on Neon

One-time per Neon branch. Neon dashboard → SQL Editor → paste:

```sql
CREATE SCHEMA IF NOT EXISTS superset_meta;
CREATE SCHEMA IF NOT EXISTS analytics;
```

Or equivalently: the full contents of `sql/neon-init.sql`.

## 5 — Bring up the stack

```bash
docker compose up --build
```

First build pulls the Superset base image (~1.2 GB, ~3–5 min on fibre). Subsequent starts take ~20s. Watch for the line `superset-init exited with code 0` — that means migrations ran and the admin user is created.

Open `http://localhost:8088`. Log in as `admin` with the password from `.env`.

## 6 — Seed the warehouse with dbt

In a second terminal:

```bash
# Install dbt-postgres (one-time)
pip install dbt-core==1.8.7 dbt-postgres==1.8.2

# Point dbt at the Neon pooled endpoint
export NEON_USER=$(awk -F: '/NEON_POOLED_URI/{print $2}' .env | sed 's|//||')
export NEON_PASSWORD=$(awk -F'[:@]' '/NEON_POOLED_URI/{print $3}' .env)

cp dbt/profiles.yml.tmpl ~/.dbt/profiles.yml
# Edit ~/.dbt/profiles.yml — set the host to your pooled hostname
#   (grep NEON_POOLED_URI .env  → the part between @ and /)

cd dbt
dbt deps
dbt seed      # loads 4 CSVs into analytics.*
dbt run       # builds staging views + marts
dbt test      # not-null, unique, relationships
```

## 7 — Register the warehouse in Superset

Superset UI → **Settings → Database Connections → + Database**:

- **Supported databases**: PostgreSQL
- **SQLAlchemy URI**: paste the value of `ANALYTICS_DB_URI` from `.env`
- **Display Name**: `Analytics (Neon)`
- **Advanced → Security → Allow DDL**: off
- **Advanced → SQL Lab**: enable

Then **Datasets → + Dataset** for each of:

- `analytics.fct_basis_margin`
- `analytics.fct_hedge_coverage`
- `analytics.fct_safex_daily`
- `analytics.dim_client`

## 8 — Author the v1 dashboards

Three dashboards to build:

- **Basis & Margin** — chart: bar of `basis_zar_per_ton` by `commodity_code`; table of top-10 `mtm_margin_zar`; KPI of total `mtm_margin_zar`.
- **SAFEX Hedge Coverage** — chart: stacked bar of `hedged_tons` vs `exposed_tons` per client; heatmap of `weighted_hedge_pct` by segment × commodity.
- **Client Book** — chart: treemap of `total_notional_zar` by client; table of `dim_client` with `credit_utilisation_pct`.

Export each dashboard (⋯ menu → Export) to `superset/assets/dashboards/*.zip` and commit. That makes the dashboards replayable on fresh deployments.

## Troubleshooting

- **`docker compose up` hangs on Superset startup** — check `superset-init` logs. Common cause: `SUPERSET_METADATA_DB_URI` pointing at the pooled endpoint. Must be the direct (no `-pooler`) host.
- **`FATAL: password authentication failed`** — the pooled URI in `secrets.txt` was a one-time view; if you re-opened Neon, the password visible there may have rotated. Grab a fresh one.
- **Charts render but show 0 rows** — you haven't run `dbt seed && dbt run` yet.
- **Port 8088 already in use** — edit `docker-compose.yml`, change the host port in `superset-web.ports`.

## Next

Once the three dashboards look good, come back and either:

- Promote to Cloud Run (`gcp/secrets-bootstrap.sh` → `./gcp/deploy-*.sh`), or
- Hand the URL to the biz-demos Cloudflare Worker to mint guest tokens and swap the static `/bi/` mockup for an iframe.
