select
    s.sku_id,
    s.sku_code,
    s.sku_name,
    s.brand,
    s.pack_size,
    s.units_per_case,
    s.cases_per_pallet,
    s.unit_price_zar,
    s.case_price_zar,
    s.shelf_life_days,
    s.requires_chilled,
    s.requires_frozen,
    s.is_own_label,
    c.category_id,
    c.category_name,
    sc.subcategory_id,
    sc.subcategory_name,
    sup.supplier_id,
    sup.supplier_name,
    sup.supplier_type,
    sup.lead_time_days,
    case
        when s.requires_frozen  then 'FROZEN'
        when s.requires_chilled then 'CHILLED'
        else                         'AMBIENT'
    end as zone
from {{ ref('stg_sku') }} s
join {{ ref('stg_category') }}   c  on s.category_id    = c.category_id
join {{ ref('stg_subcategory') }} sc on s.subcategory_id = sc.subcategory_id
join {{ ref('stg_supplier') }}   sup on s.supplier_id   = sup.supplier_id
