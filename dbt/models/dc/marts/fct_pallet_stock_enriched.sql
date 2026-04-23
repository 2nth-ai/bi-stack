with pallets as (
    select * from {{ ref('stg_pallet_stock') }}
),
skus as (
    select * from {{ ref('dim_sku_enriched') }}
),
dcs as (
    select * from {{ ref('stg_dc') }}
)
select
    p.pallet_id,
    p.dc_id,
    d.dc_name,
    d.province as dc_province,
    d.region   as dc_region,
    p.sku_id,
    s.sku_code,
    s.sku_name,
    s.brand,
    s.category_id,
    s.category_name,
    s.subcategory_id,
    s.subcategory_name,
    s.supplier_id,
    s.supplier_name,
    s.is_own_label,
    p.zone,
    p.bin_location,
    p.aisle,
    p.bay,
    p.level,
    p.pallet_type,
    p.status,
    p.qty_cases,
    p.qty_cases * s.units_per_case              as qty_units,
    round(p.qty_cases * s.case_price_zar, 2)    as stock_value_zar,
    p.received_date,
    p.best_before_date,
    (current_date - p.received_date)            as days_in_stock,
    case when p.best_before_date is not null
         then (p.best_before_date - current_date) end as days_to_best_before,
    case
        when p.best_before_date is null                        then 'NON_PERISHABLE'
        when (p.best_before_date - current_date) <= 0           then 'EXPIRED'
        when (p.best_before_date - current_date) <= 7           then 'URGENT_7D'
        when (p.best_before_date - current_date) <= 14          then 'WARN_14D'
        when (p.best_before_date - current_date) <= 30          then 'WATCH_30D'
        else                                                          'OK'
    end as expiry_bucket
from pallets p
join skus  s on p.sku_id = s.sku_id
join dcs   d on p.dc_id  = d.dc_id
