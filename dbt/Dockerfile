# dbt-core + Postgres adapter, packaged for Cloud Run Jobs.
# Entry-point runs `dbt deps && dbt build` against the Neon pooled endpoint.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DBT_PROFILES_DIR=/app

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential libpq-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir \
    dbt-core==1.8.7 \
    dbt-postgres==1.8.2

COPY dbt_project.yml packages.yml ./
COPY models ./models
COPY seeds ./seeds
COPY macros ./macros

# Rendered at runtime from env vars — see profiles.yml.tmpl for the template.
COPY profiles.yml.tmpl ./profiles.yml

RUN dbt deps || true

ENTRYPOINT ["/bin/sh", "-c", "dbt deps && dbt build --target prod"]
