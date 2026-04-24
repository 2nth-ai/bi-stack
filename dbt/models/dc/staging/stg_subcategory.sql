select
    subcategory_id,
    category_id,
    subcategory_name
from {{ ref('dim_subcategory') }}
