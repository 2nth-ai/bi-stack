with pallets as (
    select dc_id, zone, count(*) as pallets_used
    from {{ ref('stg_pallet_stock') }}
    group by 1, 2
),
dcs as (
    select * from {{ ref('stg_dc') }}
)
select
    d.dc_id,
    d.dc_name,
    d.province,
    d.region,
    d.capacity_pallets,
    p.zone,
    coalesce(p.pallets_used, 0) as pallets_used,
    round(100.0 * coalesce(p.pallets_used, 0) / nullif(d.capacity_pallets, 0), 2) as utilisation_pct
from dcs d
left join pallets p on d.dc_id = p.dc_id
