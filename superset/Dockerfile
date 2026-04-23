# Superset image for bi-stack.
# Bakes superset_config.py into the image (one-file config rule — Superset
# imports this at process start, so it cannot be mounted at runtime).
# Secrets stay as env vars injected from Secret Manager in prod.

FROM apache/superset:4.1.1

USER root

COPY requirements-local.txt /app/requirements-local.txt
RUN pip install --no-cache-dir -r /app/requirements-local.txt

COPY superset_config.py /app/pythonpath/superset_config.py
COPY bootstrap.sh /app/bootstrap.sh
RUN chmod +x /app/bootstrap.sh

ENV SUPERSET_CONFIG_PATH=/app/pythonpath/superset_config.py
ENV PYTHONPATH=/app/pythonpath:$PYTHONPATH

USER superset

EXPOSE 8088
