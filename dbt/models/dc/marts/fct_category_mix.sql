select
    dc_id,
    dc_name,
    category_id,
    category_name,
    zone,
    count(*)              as pallet_count,
    sum(qty_cases)        as qty_cases,
    sum(qty_units)        as qty_units,
    sum(stock_value_zar)  as stock_value_zar
from {{ ref('fct_pallet_stock_enriched') }}
group by 1, 2, 3, 4, 5
