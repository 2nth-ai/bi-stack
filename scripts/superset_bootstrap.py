#!/usr/bin/env python3
"""Auto-provision Superset with Neon DB + retail-DC datasets + a starter dashboard.

Idempotent:
- Registers "Analytics (Neon)" database if not present
- Creates datasets for analytics_retail_dc.fct_* / dim_sku_enriched marts
- Builds a "DC Ops Overview" dashboard with KPI tiles, pie, bar and table

Run against a local Superset at http://localhost:8088.
Admin creds read from .env.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parent.parent
BASE = "http://localhost:8088"


def env(name: str) -> str:
    for line in (REPO / ".env").read_text().splitlines():
        if line.startswith(f"{name}="):
            return line.split("=", 1)[1].strip()
    raise KeyError(name)


USER = env("ADMIN_USERNAME")
PASS = env("ADMIN_PASSWORD")
ANALYTICS_URI = env("ANALYTICS_DB_URI").replace("postgresql://", "postgresql+psycopg2://")

s = requests.Session()


def check(r: requests.Response, ctx: str) -> None:
    if not r.ok:
        print(f"  ✗ {ctx} → {r.status_code}: {r.text[:300]}")
        r.raise_for_status()


# ---------------------------------------------------------------------------
# 1. Auth
# ---------------------------------------------------------------------------
print("→ Login")
r = s.post(f"{BASE}/api/v1/security/login", json={
    "username": USER, "password": PASS, "provider": "db", "refresh": True,
})
check(r, "login")
s.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})

r = s.get(f"{BASE}/api/v1/security/csrf_token/")
check(r, "csrf")
s.headers.update({"X-CSRFToken": r.json()["result"], "Referer": BASE})


# ---------------------------------------------------------------------------
# 2. Database
# ---------------------------------------------------------------------------
def find_db(name: str) -> int | None:
    q = f"(filters:!((col:database_name,opr:eq,value:'{name}')))"
    r = s.get(f"{BASE}/api/v1/database/", params={"q": q})
    check(r, "list dbs")
    for row in r.json().get("result", []):
        if row["database_name"] == name:
            return row["id"]
    return None


DB_NAME = "Analytics (Neon)"
db_id = find_db(DB_NAME)
if db_id:
    print(f"→ DB '{DB_NAME}' exists (id={db_id})")
else:
    print(f"→ Creating DB '{DB_NAME}'")
    r = s.post(f"{BASE}/api/v1/database/", json={
        "database_name": DB_NAME,
        "sqlalchemy_uri": ANALYTICS_URI,
        "expose_in_sqllab": True,
        "allow_ctas": False,
        "allow_cvas": False,
        "allow_dml": False,
    })
    check(r, "create db")
    db_id = r.json()["id"]
    print(f"  id={db_id}")


# ---------------------------------------------------------------------------
# 3. Datasets
# ---------------------------------------------------------------------------
SCHEMA = "analytics_retail_dc"
DATASETS = [
    "dim_sku_enriched",
    "fct_pallet_stock_enriched",
    "fct_stock_movements_enriched",
    "fct_dc_utilisation",
    "fct_stock_cover_days",
    "fct_expiry_risk",
    "fct_category_mix",
    "fct_store_dc_flow",
    "fct_top_movers",
    "fct_supplier_inbound",
]


def find_dataset(table: str) -> int | None:
    q = f"(filters:!((col:table_name,opr:eq,value:'{table}')))"
    r = s.get(f"{BASE}/api/v1/dataset/", params={"q": q})
    check(r, "list datasets")
    for ds in r.json().get("result", []):
        if ds.get("schema") == SCHEMA and ds["table_name"] == table:
            return ds["id"]
    return None


ds_ids: dict[str, int] = {}
print("→ Datasets")
for table in DATASETS:
    existing = find_dataset(table)
    if existing:
        ds_ids[table] = existing
        print(f"  • {table:<35s} (existing, id={existing})")
        continue
    r = s.post(f"{BASE}/api/v1/dataset/", json={
        "database": db_id,
        "schema": SCHEMA,
        "table_name": table,
    })
    if not r.ok:
        print(f"  ✗ create {table} → {r.status_code}: {r.text[:250]}")
        continue
    ds_ids[table] = r.json()["id"]
    print(f"  • {table:<35s} (created, id={ds_ids[table]})")


# ---------------------------------------------------------------------------
# 4. Charts
#    Use simplest viz types; if a chart fails, log and continue — user can
#    recreate in the UI. Each chart gets minimum params so Superset can render.
# ---------------------------------------------------------------------------
def find_chart(name: str) -> int | None:
    q = f"(filters:!((col:slice_name,opr:eq,value:'{name}')))"
    r = s.get(f"{BASE}/api/v1/chart/", params={"q": q})
    check(r, "list charts")
    for c in r.json().get("result", []):
        if c["slice_name"] == name:
            return c["id"]
    return None


def make_metric(label: str, column: str, agg: str) -> dict:
    return {
        "expressionType": "SIMPLE",
        "column": {"column_name": column},
        "aggregate": agg,
        "label": label,
        "optionName": f"metric_{label.replace(' ', '_').lower()}",
    }


def create_chart(name: str, dataset_table: str, viz_type: str, params_extra: dict) -> int | None:
    ds_id = ds_ids.get(dataset_table)
    if not ds_id:
        print(f"  ✗ {name} → dataset {dataset_table} missing")
        return None
    existing = find_chart(name)
    if existing:
        print(f"  • {name:<40s} (existing, id={existing})")
        return existing

    params = {
        "datasource": f"{ds_id}__table",
        "viz_type": viz_type,
        "adhoc_filters": [],
        **params_extra,
    }
    body = {
        "slice_name": name,
        "viz_type": viz_type,
        "datasource_id": ds_id,
        "datasource_type": "table",
        "params": json.dumps(params),
    }
    r = s.post(f"{BASE}/api/v1/chart/", json=body)
    if not r.ok:
        print(f"  ✗ {name} → {r.status_code}: {r.text[:200]}")
        return None
    cid = r.json()["id"]
    print(f"  • {name:<40s} (created, id={cid})")
    return cid


print("→ Charts")
chart_specs = [
    # name, dataset, viz_type, extra-params
    ("DC Ops — Pallets on Hand", "fct_pallet_stock_enriched", "big_number_total", {
        "metric": make_metric("pallets", "pallet_id", "COUNT"),
        "y_axis_format": "SMART_NUMBER",
        "subheader": "Pallet positions occupied",
    }),
    ("DC Ops — Stock Value (R)", "fct_pallet_stock_enriched", "big_number_total", {
        "metric": make_metric("stock value", "stock_value_zar", "SUM"),
        "y_axis_format": "SMART_NUMBER",
        "subheader": "Total stock value on hand (ZAR)",
    }),
    ("DC Ops — SKUs Held", "fct_pallet_stock_enriched", "big_number_total", {
        "metric": {
            "expressionType": "SIMPLE",
            "column": {"column_name": "sku_id"},
            "aggregate": "COUNT_DISTINCT",
            "label": "SKUs",
            "optionName": "metric_skus_held",
        },
        "y_axis_format": "SMART_NUMBER",
        "subheader": "Distinct SKUs with stock",
    }),
    ("Stock Health — Cover Bucket Share", "fct_stock_cover_days", "pie", {
        "metric": make_metric("sku_dc_pairs", "sku_id", "COUNT"),
        "groupby": ["cover_bucket"],
        "row_limit": 10,
        "donut": False,
        "show_legend": True,
        "label_type": "key_percent",
    }),
    ("DC League — Pallets & Zone", "fct_pallet_stock_enriched", "dist_bar", {
        "metrics": [make_metric("pallets", "pallet_id", "COUNT")],
        "groupby": ["dc_name"],
        "columns": ["zone"],
        "row_limit": 100,
        "order_desc": True,
        "show_legend": True,
        "x_axis_label": "DC",
        "y_axis_label": "Pallet count",
    }),
    ("Expiry Risk — Value by Bucket", "fct_expiry_risk", "dist_bar", {
        "metrics": [make_metric("value_zar", "stock_value_zar", "SUM")],
        "groupby": ["expiry_bucket"],
        "columns": ["dc_name"],
        "row_limit": 100,
        "show_legend": True,
        "x_axis_label": "Expiry bucket",
        "y_axis_label": "Value (ZAR)",
    }),
    ("Top 20 Stockout Risks", "fct_stock_cover_days", "table", {
        "query_mode": "raw",
        "all_columns": [
            "dc_name", "sku_code", "sku_name", "category_name",
            "cases_on_hand", "avg_daily_outbound_cases", "cover_days", "cover_bucket",
        ],
        "order_by_cols": ['["avg_daily_outbound_cases", false]'],
        "row_limit": 20,
        "adhoc_filters": [{
            "clause": "WHERE",
            "expressionType": "SIMPLE",
            "subject": "cover_bucket",
            "operator": "==",
            "comparator": "STOCKOUT_RISK",
        }],
    }),
    ("Top 20 SKUs — 28d Outbound Cases", "fct_top_movers", "table", {
        "query_mode": "raw",
        "all_columns": [
            "sku_code", "sku_name", "brand", "category_name",
            "supplier_name", "is_own_label", "dc_name", "qty_cases", "value_zar",
        ],
        "order_by_cols": ['["qty_cases", false]'],
        "row_limit": 20,
    }),
    ("Category Mix — Stock Value", "fct_category_mix", "dist_bar", {
        "metrics": [make_metric("value", "stock_value_zar", "SUM")],
        "groupby": ["category_name"],
        "columns": ["zone"],
        "row_limit": 50,
        "show_legend": True,
        "bar_stacked": True,
    }),
    ("Banner Mix — 28d Outbound Value", "fct_store_dc_flow", "pie", {
        "metric": make_metric("value_zar", "value_zar", "SUM"),
        "groupby": ["banner"],
        "row_limit": 10,
        "show_legend": True,
    }),
]

chart_ids: dict[str, int] = {}
for name, ds, viz, extra in chart_specs:
    cid = create_chart(name, ds, viz, extra)
    if cid:
        chart_ids[name] = cid


# ---------------------------------------------------------------------------
# 5. Dashboard
# ---------------------------------------------------------------------------
DASHBOARD_TITLE = "Retail DC — Operations Overview"


def find_dashboard(title: str) -> int | None:
    q = f"(filters:!((col:dashboard_title,opr:eq,value:'{title}')))"
    r = s.get(f"{BASE}/api/v1/dashboard/", params={"q": q})
    check(r, "list dashboards")
    for d in r.json().get("result", []):
        if d["dashboard_title"] == title:
            return d["id"]
    return None


def build_position_json(chart_ids: dict[str, int]) -> dict:
    """Grid layout for the dashboard. 12-col grid, CHART_<id> blocks.

    Layout plan:
      Row 1: KPI tiles (3 blocks × 4 cols)
      Row 2: Pie (6 cols) + Bar (6 cols)
      Row 3: Bar (6 cols) + Pie banner (6 cols)
      Row 4: Table full width
      Row 5: Bar (full width)
      Row 6: Table full width
    """
    def k(name: str) -> str:
        cid = chart_ids.get(name)
        return f"CHART-{cid}" if cid else ""

    kpis = [
        k("DC Ops — Pallets on Hand"),
        k("DC Ops — Stock Value (R)"),
        k("DC Ops — SKUs Held"),
    ]
    pie_health = k("Stock Health — Cover Bucket Share")
    bar_dc     = k("DC League — Pallets & Zone")
    bar_expiry = k("Expiry Risk — Value by Bucket")
    pie_banner = k("Banner Mix — 28d Outbound Value")
    tbl_stock  = k("Top 20 Stockout Risks")
    tbl_movers = k("Top 20 SKUs — 28d Outbound Cases")
    bar_cat    = k("Category Mix — Stock Value")

    def chart_block(chart_code: str, width: int, height: int = 50) -> dict:
        cid = int(chart_code.split("-")[1]) if chart_code else None
        return {
            "type": "CHART",
            "id": chart_code,
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {
                "width": width,
                "height": height,
                "chartId": cid,
                "sliceName": next((n for n, i in chart_ids.items() if f"CHART-{i}" == chart_code), ""),
            },
        }

    row = lambda idx, blocks: {
        "type": "ROW",
        "id": f"ROW-{idx}",
        "children": [b["id"] for b in blocks],
        "parents": ["ROOT_ID", "GRID_ID"],
        "meta": {"background": "BACKGROUND_TRANSPARENT"},
    }

    rows_blocks = [
        [chart_block(k, 4, 30) for k in kpis if k],
        [chart_block(pie_health, 6), chart_block(bar_dc, 6)],
        [chart_block(bar_expiry, 6), chart_block(pie_banner, 6)],
        [chart_block(tbl_stock, 12, 60)],
        [chart_block(bar_cat, 12)],
        [chart_block(tbl_movers, 12, 60)],
    ]

    pos = {
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {
            "type": "GRID",
            "id": "GRID_ID",
            "children": [f"ROW-{i}" for i, _ in enumerate(rows_blocks)],
            "parents": ["ROOT_ID"],
        },
    }
    for i, blocks in enumerate(rows_blocks):
        blocks = [b for b in blocks if b["meta"]["chartId"]]
        if not blocks:
            continue
        pos[f"ROW-{i}"] = row(i, blocks)
        for b in blocks:
            pos[b["id"]] = b
    return pos


print("→ Dashboard")
dash_id = find_dashboard(DASHBOARD_TITLE)
position_json = build_position_json(chart_ids)

if dash_id:
    print(f"  exists (id={dash_id}), updating position")
    r = s.put(f"{BASE}/api/v1/dashboard/{dash_id}", json={
        "position_json": json.dumps(position_json),
    })
    check(r, "update dashboard")
else:
    print("  creating…")
    r = s.post(f"{BASE}/api/v1/dashboard/", json={
        "dashboard_title": DASHBOARD_TITLE,
        "slug": "retail-dc-ops",
        "published": True,
        "position_json": json.dumps(position_json),
    })
    check(r, "create dashboard")
    dash_id = r.json()["id"]
    print(f"  id={dash_id}")

# ---------------------------------------------------------------------------
# 6. Attach charts to dashboard (PUT chart.dashboards = [dash_id])
# ---------------------------------------------------------------------------
print("→ Linking charts → dashboard")
for name, cid in chart_ids.items():
    # Read current chart to preserve other dashboard associations
    r = s.get(f"{BASE}/api/v1/chart/{cid}")
    if not r.ok:
        print(f"  ✗ read chart {cid}: {r.status_code}")
        continue
    existing = {d["id"] for d in r.json()["result"].get("dashboards", [])}
    existing.add(dash_id)
    r = s.put(f"{BASE}/api/v1/chart/{cid}", json={"dashboards": list(existing)})
    if not r.ok:
        print(f"  ✗ link {name} → {r.status_code}: {r.text[:200]}")
    else:
        print(f"  • linked {name}")

print()
print(f"✓ All set. Open: {BASE}/superset/dashboard/retail-dc-ops/")
print(f"  (or id {dash_id}: {BASE}/superset/dashboard/{dash_id}/)")
