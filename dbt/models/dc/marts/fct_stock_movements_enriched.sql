with m as (
    select * from {{ ref('stg_stock_movements') }}
),
skus as (
    select * from {{ ref('dim_sku_enriched') }}
),
dcs as (
    select * from {{ ref('stg_dc') }}
),
stores as (
    select * from {{ ref('stg_store') }}
),
suppliers as (
    select * from {{ ref('stg_supplier') }}
)
select
    m.movement_id,
    m.movement_date,
    date_trunc('week', m.movement_date)::date as iso_week_start,
    to_char(m.movement_date, 'Dy')            as day_of_week,
    m.movement_type,
    m.dc_id,
    d.dc_name,
    d.province as dc_province,
    d.region   as dc_region,
    m.sku_id,
    s.sku_code,
    s.sku_name,
    s.brand,
    s.category_id,
    s.category_name,
    s.subcategory_name,
    s.zone,
    s.is_own_label,
    m.supplier_id,
    sup.supplier_name,
    sup.supplier_type,
    m.store_id,
    st.banner,
    st.store_name,
    st.province_code as store_province,
    m.qty_cases,
    m.qty_units,
    m.unit_price_zar,
    m.line_value_zar,
    m.document_number
from m
join dcs  d on m.dc_id = d.dc_id
join skus s on m.sku_id = s.sku_id
left join stores    st  on m.store_id    = st.store_id
left join suppliers sup on m.supplier_id = sup.supplier_id
