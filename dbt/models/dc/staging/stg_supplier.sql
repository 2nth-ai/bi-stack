select
    supplier_id,
    supplier_code,
    supplier_name,
    category_ids,
    supplier_type,
    payment_terms,
    lead_time_days
from {{ ref('dim_supplier') }}
