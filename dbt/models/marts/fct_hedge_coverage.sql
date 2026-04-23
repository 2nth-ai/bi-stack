-- Hedge coverage by client × commodity: total tons, hedged tons, exposed tons,
-- and weighted-average hedge percentage.

with contracts as (
    select
        client_id,
        commodity_code,
        tons,
        tons * (hedge_pct / 100.0) as hedged_tons,
        tons * (1 - hedge_pct / 100.0) as exposed_tons,
        notional_zar,
        hedge_pct
    from {{ ref('stg_contract_book') }}
)

select
    cl.client_id,
    cl.client_name,
    cl.segment,
    c.commodity_code,
    sum(c.tons) as total_tons,
    sum(c.hedged_tons) as hedged_tons,
    sum(c.exposed_tons) as exposed_tons,
    round(
        case when sum(c.tons) = 0 then 0
             else (sum(c.hedged_tons) / sum(c.tons)) * 100
        end, 2
    ) as weighted_hedge_pct,
    sum(c.notional_zar) as notional_zar
from contracts c
join {{ ref('dim_client') }} cl using (client_id)
group by 1, 2, 3, 4
