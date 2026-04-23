select
    dc_id,
    dc_code,
    dc_name,
    city,
    province,
    region,
    zones,
    capacity_pallets,
    temp_profile
from {{ ref('dim_dc') }}
