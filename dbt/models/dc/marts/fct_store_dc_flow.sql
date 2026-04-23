select
    date_trunc('week', movement_date)::date as iso_week_start,
    dc_id,
    dc_name,
    dc_province,
    store_id,
    banner,
    store_province,
    category_id,
    category_name,
    sum(qty_cases)      as qty_cases,
    sum(qty_units)      as qty_units,
    sum(line_value_zar) as value_zar
from {{ ref('fct_stock_movements_enriched') }}
where movement_type = 'OUTBOUND'
  and store_id is not null
group by 1, 2, 3, 4, 5, 6, 7, 8, 9
