with source as (
    select * from {{ ref('feedlot_rations') }}
)

select
    ration_id,
    client_id,
    ration_name,
    yellow_maize_pct,
    soybean_meal_pct,
    wheat_bran_pct,
    sunflower_meal_pct,
    hominy_chop_pct,
    urea_pct,
    minerals_pct,
    cost_per_ton_zar
from source
