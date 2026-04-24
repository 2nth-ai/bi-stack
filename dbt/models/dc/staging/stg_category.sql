select
    category_id,
    category_name,
    default_zone
from {{ ref('dim_category') }}
