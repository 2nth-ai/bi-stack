-- Rolling SAFEX price table for trend charts. Adds 7-day moving average
-- and day-on-day delta per commodity.

with base as (
    select
        trade_date,
        commodity_code,
        commodity_name,
        contract_month,
        settlement_zar_per_ton,
        volume_tons
    from {{ ref('stg_safex_prices') }}
)

select
    trade_date,
    commodity_code,
    commodity_name,
    contract_month,
    settlement_zar_per_ton,
    volume_tons,
    settlement_zar_per_ton - lag(settlement_zar_per_ton) over (
        partition by commodity_code order by trade_date
    ) as dod_change_zar,
    avg(settlement_zar_per_ton) over (
        partition by commodity_code order by trade_date
        rows between 6 preceding and current row
    ) as ma7_zar_per_ton
from base
