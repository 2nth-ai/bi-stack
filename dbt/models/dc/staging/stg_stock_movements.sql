select
    movement_id,
    movement_date,
    movement_type,
    dc_id,
    sku_id,
    nullif(supplier_id::text, '')::int as supplier_id,
    nullif(store_id::text, '')::int    as store_id,
    qty_cases,
    qty_units,
    unit_price_zar,
    line_value_zar,
    document_number
from {{ source('retail_dc_raw', 'raw_stock_movements') }}
