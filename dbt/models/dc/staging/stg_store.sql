select
    store_id,
    store_code,
    banner,
    store_name,
    province_code,
    province_name,
    city,
    primary_dc_id,
    trading_area_sqm,
    open_date,
    status
from {{ ref('dim_store') }}
