{#
  Stock cover = (current pallet cases) / (avg daily outbound cases over last 28 days)
  Flags: <7d stockout risk; >45d slow-mover.
#}

with on_hand as (
    select
        p.dc_id,
        p.sku_id,
        sum(p.qty_cases) as cases_on_hand
    from {{ ref('stg_pallet_stock') }} p
    where p.status in ('PICKABLE', 'RESERVE')
    group by 1, 2
),
outbound_28d as (
    select
        m.dc_id,
        m.sku_id,
        sum(m.qty_cases) / 28.0 as avg_daily_outbound_cases
    from {{ ref('stg_stock_movements') }} m
    where m.movement_type = 'OUTBOUND'
      and m.movement_date >= current_date - interval '28 days'
    group by 1, 2
),
skus as (
    select * from {{ ref('dim_sku_enriched') }}
),
dcs as (
    select * from {{ ref('stg_dc') }}
)
select
    d.dc_id,
    d.dc_name,
    d.province,
    s.sku_id,
    s.sku_code,
    s.sku_name,
    s.brand,
    s.category_name,
    s.subcategory_name,
    s.supplier_name,
    s.is_own_label,
    coalesce(o.cases_on_hand, 0)                as cases_on_hand,
    round(coalesce(ob.avg_daily_outbound_cases, 0), 2) as avg_daily_outbound_cases,
    case
        when coalesce(ob.avg_daily_outbound_cases, 0) = 0 then null
        else round(coalesce(o.cases_on_hand, 0) / ob.avg_daily_outbound_cases, 1)
    end as cover_days,
    case
        when coalesce(ob.avg_daily_outbound_cases, 0) = 0                               then 'NON_MOVING'
        when coalesce(o.cases_on_hand, 0) / ob.avg_daily_outbound_cases < 7              then 'STOCKOUT_RISK'
        when coalesce(o.cases_on_hand, 0) / ob.avg_daily_outbound_cases between 7 and 21 then 'HEALTHY'
        when coalesce(o.cases_on_hand, 0) / ob.avg_daily_outbound_cases between 21 and 45 then 'BUFFER'
        else                                                                              'OVERSTOCK'
    end as cover_bucket
from dcs d
cross join skus s
left join on_hand       o  on d.dc_id = o.dc_id  and s.sku_id = o.sku_id
left join outbound_28d  ob on d.dc_id = ob.dc_id and s.sku_id = ob.sku_id
where coalesce(o.cases_on_hand, 0) + coalesce(ob.avg_daily_outbound_cases, 0) > 0
