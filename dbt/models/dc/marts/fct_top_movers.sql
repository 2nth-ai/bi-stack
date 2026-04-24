with last_28 as (
    select
        dc_id,
        dc_name,
        sku_id,
        sku_code,
        sku_name,
        brand,
        category_id,
        category_name,
        supplier_name,
        is_own_label,
        zone,
        sum(qty_cases)      as qty_cases,
        sum(qty_units)      as qty_units,
        sum(line_value_zar) as value_zar
    from {{ ref('fct_stock_movements_enriched') }}
    where movement_type = 'OUTBOUND'
      and movement_date >= current_date - interval '28 days'
    group by 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
),
ranked as (
    select
        *,
        row_number() over (partition by dc_id order by qty_cases desc) as rank_in_dc,
        row_number() over (                   order by qty_cases desc) as rank_overall
    from last_28
)
select * from ranked where rank_in_dc <= 100
