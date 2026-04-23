select
    pallet_id,
    dc_id,
    sku_id,
    zone,
    bin_location,
    aisle,
    bay,
    level,
    qty_cases,
    received_date,
    best_before_date,
    pallet_type,
    status
from {{ ref('fct_pallet_stock') }}
