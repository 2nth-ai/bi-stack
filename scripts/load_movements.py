#!/usr/bin/env python3
"""Bulk-load fct_stock_movements into Neon via psycopg2 COPY.

Too big for dbt seed (~200k rows over trans-Atlantic latency would take hours).
Creates `analytics_retail_dc.raw_stock_movements` and COPYs the CSV in one go.

Idempotent: drops + recreates the raw table.
"""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg2

REPO = Path(__file__).resolve().parent.parent
ENV_FILE = REPO / ".env"
CSV_PATH = REPO / "scripts" / "out" / "fct_stock_movements.csv"


def read_uri_from_env() -> str:
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith("ANALYTICS_DB_URI="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("ANALYTICS_DB_URI not found in .env")


DDL = """
CREATE SCHEMA IF NOT EXISTS analytics_retail_dc;

DROP TABLE IF EXISTS analytics_retail_dc.raw_stock_movements CASCADE;

CREATE TABLE analytics_retail_dc.raw_stock_movements (
    movement_id      bigint PRIMARY KEY,
    movement_date    date          NOT NULL,
    movement_type    varchar(16)   NOT NULL,
    dc_id            int           NOT NULL,
    sku_id           int           NOT NULL,
    supplier_id      int,
    store_id         int,
    qty_cases        int           NOT NULL,
    qty_units        int           NOT NULL,
    unit_price_zar   numeric(12,2) NOT NULL,
    line_value_zar   numeric(14,2) NOT NULL,
    document_number  varchar(32)
);

CREATE INDEX idx_raw_movements_date     ON analytics_retail_dc.raw_stock_movements (movement_date);
CREATE INDEX idx_raw_movements_dc_sku   ON analytics_retail_dc.raw_stock_movements (dc_id, sku_id);
CREATE INDEX idx_raw_movements_type     ON analytics_retail_dc.raw_stock_movements (movement_type);
"""

COPY_SQL = """
COPY analytics_retail_dc.raw_stock_movements
    (movement_id, movement_date, movement_type, dc_id, sku_id,
     supplier_id, store_id, qty_cases, qty_units,
     unit_price_zar, line_value_zar, document_number)
FROM STDIN
WITH (FORMAT CSV, HEADER TRUE, NULL '');
"""


def main() -> int:
    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found. Run scripts/generate_retail_dc.py first.")
        return 1

    uri = read_uri_from_env()
    size_mb = CSV_PATH.stat().st_size / 1024 / 1024
    print(f"source: {CSV_PATH.relative_to(REPO)} ({size_mb:.1f} MB)")

    with psycopg2.connect(uri) as conn:
        with conn.cursor() as cur:
            print("creating table…")
            cur.execute(DDL)
            conn.commit()

            print("streaming COPY…")
            with CSV_PATH.open("r") as f:
                cur.copy_expert(COPY_SQL, f)
            conn.commit()

            cur.execute("SELECT count(*) FROM analytics_retail_dc.raw_stock_movements")
            (n,) = cur.fetchone()
            print(f"loaded {n:,} rows into analytics_retail_dc.raw_stock_movements")

            cur.execute(
                "SELECT movement_type, count(*) "
                "FROM analytics_retail_dc.raw_stock_movements GROUP BY 1 ORDER BY 1"
            )
            for kind, cnt in cur.fetchall():
                print(f"  {kind:10s} {cnt:>10,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
