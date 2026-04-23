with source as (
    select * from {{ ref('safex_prices') }}
)

select
    trade_date,
    commodity_code,
    commodity_name,
    contract_month,
    settlement_zar_per_ton,
    volume_tons
from source
