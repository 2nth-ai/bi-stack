with source as (
    select * from {{ ref('contract_book') }}
)

select
    contract_id,
    client_id,
    commodity_code,
    side,
    tons,
    price_zar_per_ton,
    tons * price_zar_per_ton as notional_zar,
    delivery_date,
    hedge_pct,
    currency
from source
