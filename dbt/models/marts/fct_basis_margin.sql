-- Basis = contract price minus latest SAFEX settle (per commodity).
-- Positive basis = we sold above market (good on a SELL); negative = we bought
-- below market (good on a BUY).

with latest_settle as (
    select
        commodity_code,
        settlement_zar_per_ton as latest_settle_zar_per_ton,
        trade_date as latest_settle_date
    from (
        select
            commodity_code,
            settlement_zar_per_ton,
            trade_date,
            row_number() over (partition by commodity_code order by trade_date desc) as rn
        from {{ ref('stg_safex_prices') }}
    ) t
    where rn = 1
),

contracts as (
    select
        cb.contract_id,
        cb.client_id,
        cb.commodity_code,
        cb.side,
        cb.tons,
        cb.price_zar_per_ton,
        cb.notional_zar,
        cb.delivery_date,
        cb.hedge_pct
    from {{ ref('stg_contract_book') }} cb
)

select
    c.contract_id,
    c.client_id,
    cl.client_name,
    cl.segment,
    c.commodity_code,
    c.side,
    c.tons,
    c.price_zar_per_ton,
    s.latest_settle_zar_per_ton,
    s.latest_settle_date,
    c.price_zar_per_ton - s.latest_settle_zar_per_ton as basis_zar_per_ton,
    case c.side
        when 'BUY'  then (s.latest_settle_zar_per_ton - c.price_zar_per_ton) * c.tons
        when 'SELL' then (c.price_zar_per_ton - s.latest_settle_zar_per_ton) * c.tons
    end as mtm_margin_zar,
    c.notional_zar,
    c.hedge_pct,
    c.delivery_date
from contracts c
join latest_settle s using (commodity_code)
join {{ ref('dim_client') }} cl using (client_id)
