select
    dc_id,
    dc_name,
    dc_province,
    category_id,
    category_name,
    subcategory_name,
    expiry_bucket,
    count(*)               as pallet_count,
    sum(qty_cases)         as qty_cases,
    sum(qty_units)         as qty_units,
    sum(stock_value_zar)   as stock_value_zar
from {{ ref('fct_pallet_stock_enriched') }}
where expiry_bucket in ('EXPIRED', 'URGENT_7D', 'WARN_14D', 'WATCH_30D')
group by 1, 2, 3, 4, 5, 6, 7
