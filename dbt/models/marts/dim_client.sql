with clients as (
    select * from {{ ref('stg_clients') }}
),

contracts as (
    select
        client_id,
        count(*) as open_contracts,
        sum(notional_zar) as total_notional_zar,
        avg(hedge_pct) as avg_hedge_pct
    from {{ ref('stg_contract_book') }}
    group by 1
)

select
    c.client_id,
    c.client_name,
    c.segment,
    c.region,
    c.credit_limit_zar,
    coalesce(x.open_contracts, 0) as open_contracts,
    coalesce(x.total_notional_zar, 0) as total_notional_zar,
    x.avg_hedge_pct,
    case
        when x.total_notional_zar is null then 0
        else round((x.total_notional_zar / c.credit_limit_zar) * 100, 2)
    end as credit_utilisation_pct
from clients c
left join contracts x using (client_id)
